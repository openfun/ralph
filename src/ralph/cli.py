"""Ralph CLI entrypoint"""

import json
import logging
import re
import sys

import click
import uvicorn
from click_option_group import optgroup
from pydantic import BaseModel

from ralph.conf import settings
from ralph.exceptions import UnsupportedBackendException
from ralph.logger import configure_logging
from ralph.models.converter import Converter
from ralph.models.selector import ModelSelector
from ralph.models.validator import Validator
from ralph.utils import get_backend_instance, get_backend_type, get_root_logger

# cli module logger
logger = logging.getLogger(__name__)


class CommaSeparatedKeyValueParamType(click.ParamType):
    """Comma separated key=value parameter type."""

    name = "key=value,key=value"

    def convert(self, value, param, ctx):
        """Split value by comma and equal sign to return a dict build with key/value
        pairs.
        """

        if isinstance(value, dict):
            return value

        # Parse options string
        try:
            options = dict(option.split("=") for option in value.split(","))
        except ValueError:
            self.fail(
                (
                    "You should provide key=value pairs separated by commas, "
                    "e.g. foo=bar,bar=2"
                ),
                param,
                ctx,
            )

        # Cast simple types
        for key, value_ in options.items():
            if value_ == "":
                options.update({key: None})
            elif re.match("^true$", value_, re.IGNORECASE):
                options.update({key: True})
            elif re.match("^false$", value_, re.IGNORECASE):
                options.update({key: False})
            elif re.match(r"^[0-9]+\.[0-9]+$", value_):
                options.update({key: float(value_)})
            elif re.match("^[0-9]+$", value_):
                options.update({key: int(value_)})

        return options


class JSONStringParamType(click.ParamType):
    """JSON string parameter type."""

    name = '\'{"key": "value", "key": "value"}\''

    def convert(self, value, param, ctx):
        """Load value as a json string and return a dict."""

        try:
            options = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            self.fail(
                ("You should provide a valid JSON string as input"),
                param,
                ctx,
            )
        return options


@click.group(name="ralph")
@click.option(
    "-v",
    "--verbosity",
    type=click.Choice(["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"]),
    metavar="LVL",
    required=False,
    help="Either CRITICAL, ERROR, WARNING, INFO (default) or DEBUG",
)
def cli(verbosity=None):
    """Ralph is a stream-based tool to play with your logs."""

    configure_logging()
    if verbosity is not None:
        level = getattr(logging, verbosity, None)
        get_root_logger().setLevel(level)
        for handler in get_root_logger().handlers:
            handler.setLevel(level)


def backends_options(name=None, backend_types: list[BaseModel] = None):
    """Backend-related options decorator for Ralph commands."""

    def wrapper(command):
        backend_names = []
        for backend_type in backend_types:
            for backend_name, backend in backend_type:
                backend_name = backend_name.lower()
                backend_names.append(backend_name)
                for field_name, field in backend:
                    field_type = backend.__fields__[field_name].type_
                    field_name = f"{backend_name}-{field_name}".replace("_", "-")
                    option = f"--{field_name}"
                    option_kwargs = {}
                    # If the field is a boolean, convert it to a flag option
                    if field_type is bool:
                        option = f"{option}/--no-{field_name}"
                        option_kwargs["is_flag"] = True
                    elif field_type is dict:
                        option_kwargs["type"] = CommaSeparatedKeyValueParamType()

                    command = optgroup.option(
                        option.lower(), default=field, **option_kwargs
                    )(command)

                command = (optgroup.group(f"{backend_name} backend"))(command)

        command = click.option(
            "-b",
            "--backend",
            type=click.Choice(backend_names),
            required=True,
            help="Backend",
        )(command)

        command = (cli.command(name=name or command.__name__))(command)
        return command

    return wrapper


@cli.command()
@click.option(
    "-p",
    "--parser",
    type=click.Choice([parser.lower() for parser, _ in settings.PARSERS]),
    required=True,
    help="Container format parser used to extract events",
)
def extract(parser):
    """Extracts input events from a container format using a dedicated parser."""

    logger.info("Extracting events using the %s parser", parser)

    parser = getattr(settings.PARSERS, parser.upper()).get_instance()

    for event in parser.parse(sys.stdin):
        click.echo(event)


@cli.command()
@click.option(
    "-f",
    "--format",
    "format_",
    type=click.Choice(["edx", "xapi"]),
    required=True,
    help="Input events format to validate",
)
@click.option(
    "-I",
    "--ignore-errors",
    default=False,
    is_flag=True,
    help="Continue validating regardless of raised errors",
)
@click.option(
    "-F",
    "--fail-on-unknown",
    default=False,
    is_flag=True,
    help="Stop validating at first unknown event",
)
def validate(format_, ignore_errors, fail_on_unknown):
    """Validates input events of given format."""

    logger.info(
        "Validating %s events (ignore_errors=%s | fail-on-unknown=%s)",
        format_,
        ignore_errors,
        fail_on_unknown,
    )

    validator = Validator(ModelSelector(f"ralph.models.{format_}"))

    for event in validator.validate(sys.stdin, ignore_errors, fail_on_unknown):
        click.echo(event)


@cli.command()
@optgroup.group("From edX to xAPI converter options")
@optgroup.option(
    "-u",
    "--uuid-namespace",
    type=str,
    required=False,
    default=settings.CONVERTER_EDX_XAPI_UUID_NAMESPACE,
    help="The UUID namespace to use for the `ID` field generation",
)
@optgroup.option(
    "-p",
    "--platform-url",
    type=str,
    required=True,
    help="The `actor.account.homePage` to use in the xAPI statements",
)
@click.option(
    "-f",
    "--from",
    "from_",
    type=click.Choice(["edx"]),
    required=True,
    help="Input events format to convert",
)
@click.option(
    "-t",
    "--to",
    "to_",
    type=click.Choice(["xapi"]),
    required=True,
    help="Output events format",
)
@click.option(
    "-I",
    "--ignore-errors",
    default=False,
    is_flag=True,
    help="Continue writing regardless of raised errors",
)
@click.option(
    "-F",
    "--fail-on-unknown",
    default=False,
    is_flag=True,
    help="Stop converting at first unknown event",
)
def convert(from_, to_, ignore_errors, fail_on_unknown, **conversion_set_kwargs):
    """Converts input events to a given format."""

    logger.info(
        "Converting %s events to %s format (ignore_errors=%s | fail-on-unknown=%s)",
        from_,
        to_,
        ignore_errors,
        fail_on_unknown,
    )
    logger.debug("Converter parameters: %s", conversion_set_kwargs)

    converter = Converter(
        model_selector=ModelSelector(f"ralph.models.{from_}"),
        module=f"ralph.models.{from_}.converters.{to_}",
        **conversion_set_kwargs,
    )

    for event in converter.convert(sys.stdin, ignore_errors, fail_on_unknown):
        click.echo(event)


@click.argument("archive", required=False)
@backends_options(backend_types=[backend for _, backend in settings.BACKENDS])
@click.option(
    "-c",
    "--chunk-size",
    type=int,
    default=settings.DEFAULT_BACKEND_CHUNK_SIZE,
    help="Get events by chunks of size #",
)
@click.option(
    "-q",
    "--query",
    type=JSONStringParamType(),
    default=None,
    help="Query object as a JSON string (database backends ONLY)",
)
def fetch(backend, archive, chunk_size, query, **options):
    """Fetch an archive or records from a configured backend."""

    logger.info(
        (
            "Fetching data from the configured %s backend "
            "(archive: %s | chunk size: %s | query: %s)"
        ),
        backend,
        archive,
        chunk_size,
        query,
    )
    logger.debug("Backend parameters: %s", options)

    backend_type = get_backend_type(settings.BACKENDS, backend)
    backend = get_backend_instance(backend_type, backend, options)

    if backend_type == settings.BACKENDS.STORAGE:
        for data in backend.read(archive, chunk_size=chunk_size):
            click.echo(data, nl=False)
    elif backend_type == settings.BACKENDS.DATABASE:
        if query is not None:
            query = backend.query_model.parse_obj(query)
        for document in backend.get(query=query, chunk_size=chunk_size):
            click.echo(
                bytes(
                    json.dumps(document) if isinstance(document, dict) else document,
                    encoding="utf-8",
                )
            )
    elif backend_type == settings.BACKENDS.STREAM:
        backend.stream(sys.stdout.buffer)
    elif backend_type is None:
        msg = "Cannot find an implemented backend type for backend %s"
        logger.error(msg, backend)
        raise UnsupportedBackendException(msg, backend)


# pylint: disable=unnecessary-direct-lambda-call
@click.argument("archive", required=False)
@backends_options(backend_types=[settings.BACKENDS.DATABASE, settings.BACKENDS.STORAGE])
@click.option(
    "-c",
    "--chunk-size",
    type=int,
    default=settings.DEFAULT_BACKEND_CHUNK_SIZE,
    help="Get events by chunks of size #",
)
@click.option(
    "-f",
    "--force",
    default=False,
    is_flag=True,
    help="Overwrite existing archives or records",
)
@click.option(
    "-I",
    "--ignore-errors",
    default=False,
    is_flag=True,
    help="Continue writing regardless of raised errors",
)
def push(backend, archive, chunk_size, force, ignore_errors, **options):
    """Push an archive to a configured backend."""

    logger.info("Pushing archive %s to the configured %s backend", archive, backend)
    logger.debug("Backend parameters: %s", options)

    backend_type = get_backend_type(settings.BACKENDS, backend)
    backend = get_backend_instance(backend_type, backend, options)

    if backend_type == settings.BACKENDS.STORAGE:
        backend.write(sys.stdin.buffer, archive, overwrite=force)
    elif backend_type == settings.BACKENDS.DATABASE:
        backend.put(sys.stdin, chunk_size=chunk_size, ignore_errors=ignore_errors)
    elif backend_type is None:
        msg = "Cannot find an implemented backend type for backend %s"
        logger.error(msg, backend)
        raise UnsupportedBackendException(msg, backend)


@backends_options(name="list", backend_types=[settings.BACKENDS.STORAGE])
@click.option(
    "-n/-a",
    "--new/--all",
    default=False,
    help="List not fetched (or all) archives",
)
@click.option(
    "-D/-I",
    "--details/--ids",
    default=False,
    help="Get archives detailed output (JSON)",
)
def list_(details, new, backend, **options):
    """List available archives from a configured storage backend."""

    logger.info("Listing archives for the configured %s backend", backend)
    logger.debug("Fetch details: %s", str(details))
    logger.debug("Backend parameters: %s", options)

    storage = get_backend_instance(settings.BACKENDS.STORAGE, backend, options)

    archives = storage.list(details=details, new=new)

    counter = 0
    for archive in archives:
        click.echo(json.dumps(archive) if details else archive)
        counter += 1

    if counter == 0:
        logger.warning("Configured %s backend contains no archive", backend)


@cli.command()
@click.option(
    "-h",
    "--host",
    type=str,
    required=False,
    default=settings.RUNSERVER_HOST,
    help="LRS server host name",
)
@click.option(
    "-p",
    "--port",
    type=int,
    required=False,
    default=settings.RUNSERVER_PORT,
    help="LRS server port",
)
def runserver(host: str, port: int):
    """Runs the API server for the development environment.

    Starts uvicorn programmatically for convenience and documentation.
    """

    logger.info("Running API server on %s:%s.", host, port)
    logger.info(
        (
            "Do not use runserver in production - start production servers "
            "through a process manager such as gunicorn/supervisor/circus."
        )
    )
    uvicorn.run(
        "ralph.api:app",
        host=host,
        port=port,
        log_level="debug",
        reload=True,
    )
    logger.info("Shutting down uvicorn server.")
