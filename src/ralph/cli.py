"""Ralph CLI entrypoint"""

import json
import logging
import re
import sys
from inspect import signature

import click
from click_option_group import optgroup

from ralph.backends import BackendTypes
from ralph.defaults import (
    CONVERTER_EDX_XAPI_UUID_NAMESPACE,
    DEFAULT_BACKEND_CHUNK_SIZE,
    ENVVAR_PREFIX,
    DatabaseBackends,
    Parsers,
    StorageBackends,
)
from ralph.exceptions import UnsupportedBackendException
from ralph.logger import configure_logging
from ralph.models.converter import Converter
from ralph.models.selector import ModelSelector
from ralph.models.validator import Validator
from ralph.utils import (
    get_backend_type,
    get_class_from_name,
    get_class_names,
    get_instance_from_class,
    get_root_logger,
)

# cli module logger
logger = logging.getLogger(__name__)

# Lazy evaluations
DATABASE_BACKENDS = (lambda: [backend.value for backend in DatabaseBackends])()
PARSERS = (lambda: [parser.value for parser in Parsers])()
STORAGE_BACKENDS = (lambda: [backend.value for backend in StorageBackends])()
BACKENDS = (lambda: DATABASE_BACKENDS + STORAGE_BACKENDS)()


class CommaSeparatedKeyValueParamType(click.ParamType):
    """Comma separated key=value parameter type."""

    name = "key=value,key=value"

    def convert(self, value, param, ctx):
        """Split value by comma and equal sign to return a dict build with key/value pairs."""

        # Parse options string
        try:
            options = dict(option.split("=") for option in value.split(","))
        except ValueError:
            self.fail(
                "You should provide key=value pairs separated by commas, e.g. foo=bar,bar=2",
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


def backends_options(name=None, backends=None):
    """Backend-related options decorator for Ralph commands."""

    backend_names = get_class_names(backends)

    def wrapper(command):
        command = (
            click.option(
                "-b",
                "--backend",
                type=click.Choice(backend_names),
                required=True,
                help="Backend",
            )
        )(command)

        for backend_name in backend_names:
            backend_class = get_class_from_name(backend_name, backends)

            for parameter in signature(backend_class.__init__).parameters.values():
                if parameter.name == "self":
                    continue
                option = f"--{backend_class.name}-{parameter.name}".replace("_", "-")
                envvar = (
                    f"{ENVVAR_PREFIX}_{backend_class.name}_{parameter.name}".upper()
                )
                option_kwargs = {}
                # If the parameter is a boolean, convert it to a flag option
                if parameter.annotation is bool:
                    option = (
                        f"{option}/--no-{backend_class.name}-{parameter.name}".replace(
                            "_", "-"
                        )
                    )
                    option_kwargs["is_flag"] = True
                elif parameter.annotation is dict:
                    option_kwargs["type"] = CommaSeparatedKeyValueParamType()
                command = (
                    optgroup.option(
                        option,
                        envvar=envvar,
                        default=parameter.default,
                        **option_kwargs,
                    )
                )(command)
            command = (optgroup.group(f"{backend_class.name} backend"))(command)

        command = (cli.command(name=name or command.__name__))(command)
        return command

    return wrapper


@cli.command()
@click.option(
    "-p",
    "--parser",
    type=click.Choice(get_class_names(PARSERS)),
    required=True,
    help="Container format parser used to extract events",
)
def extract(parser):
    """Extracts input events from a container format using a dedicated parser."""

    logger.info("Extracting events using the %s parser", parser)

    parser = get_class_from_name(parser, PARSERS)()

    for event in parser.parse(sys.stdin):
        click.echo(event)


@cli.command()
@click.option(
    "-f",
    "--format",
    "format_",
    type=click.Choice(["edx"]),
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
    default=CONVERTER_EDX_XAPI_UUID_NAMESPACE,
    help="The UUID namespace to use for the `ID` field generation",
)
@optgroup.option(
    "-h",
    "--home_page",
    type=str,
    required=False,
    default="https://fun-mooc.fr",
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
@backends_options(backends=BACKENDS)
@click.option(
    "-c",
    "--chunk-size",
    type=int,
    default=DEFAULT_BACKEND_CHUNK_SIZE,
    help="Get events by chunks of size #",
)
def fetch(backend, archive, chunk_size, **options):
    """Fetch an archive or records from a configured backend."""

    logger.info(
        "Fetching data from the configured %s backend (archive: %s | chunk size: %s)",
        backend,
        archive,
        chunk_size,
    )
    logger.debug("Backend parameters: %s", options)

    backend_class = get_class_from_name(backend, BACKENDS)
    backend = get_instance_from_class(backend_class, **options)
    backend_type = get_backend_type(backend_class)

    if backend_type == BackendTypes.STORAGE:
        backend.read(archive, chunk_size=chunk_size)
    elif backend_type == BackendTypes.DATABASE:
        backend.get(chunk_size=chunk_size)
    elif backend_type is None:
        msg = "Cannot find an implemented backend type for backend %s"
        logger.error(msg, backend)
        raise UnsupportedBackendException(msg, backend)


@click.argument("archive", required=False)
@backends_options(backends=BACKENDS)
@click.option(
    "-c",
    "--chunk-size",
    type=int,
    default=DEFAULT_BACKEND_CHUNK_SIZE,
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

    backend_class = get_class_from_name(backend, BACKENDS)
    backend = get_instance_from_class(backend_class, **options)
    backend_type = get_backend_type(backend_class)

    if backend_type == BackendTypes.STORAGE:
        backend.write(archive, overwrite=force)
    elif backend_type == BackendTypes.DATABASE:
        backend.put(chunk_size=chunk_size, ignore_errors=ignore_errors)
    elif backend_type is None:
        msg = "Cannot find an implemented backend type for backend %s"
        logger.error(msg, backend)
        raise UnsupportedBackendException(msg, backend)


@backends_options(name="list", backends=STORAGE_BACKENDS)
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

    storage = get_instance_from_class(
        get_class_from_name(backend, STORAGE_BACKENDS), **options
    )
    archives = storage.list(details=details, new=new)

    counter = 0
    for archive in archives:
        click.echo(json.dumps(archive) if details else archive)
        counter += 1

    if counter == 0:
        logger.warning("Configured %s backend contains no archive", backend)
