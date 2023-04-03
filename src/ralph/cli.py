"""Ralph CLI entrypoint."""

import json
import logging
import re
import sys
from inspect import isclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import List

import bcrypt

try:
    import click
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(
        "You need to install 'cli' optional dependencies to use the ralph "
        "command: pip install ralph-malph[cli]"
    ) from err
try:
    import uvicorn
except ModuleNotFoundError:
    # This error will be catched in the runserver command. We should be able to
    # use all commands except the runserver command when lrs optional
    # dependencies are not installed.
    pass
from click_option_group import optgroup
from pydantic import BaseModel

from ralph import __version__ as ralph_version
from ralph.conf import ClientOptions, CommaSeparatedTuple, HeadersParameters, settings
from ralph.exceptions import UnsupportedBackendException
from ralph.logger import configure_logging
from ralph.models.converter import Converter
from ralph.models.selector import ModelSelector
from ralph.models.validator import Validator
from ralph.utils import (
    get_backend_instance,
    get_backend_type,
    get_root_logger,
    import_string,
)

# cli module logger
logger = logging.getLogger(__name__)


class CommaSeparatedTupleParamType(click.ParamType):
    """Comma separated tuple parameter type."""

    name = "value1,value2,value3"

    def convert(self, value, param, ctx):
        """Splits the value by comma to return a tuple of values."""
        if isinstance(value, str):
            return tuple(value.split(","))

        if not isinstance(value, tuple):
            self.fail(
                "You should provide values separated by commas, e.g. foo,bar,baz",
                param,
                ctx,
            )

        return value


class CommaSeparatedKeyValueParamType(click.ParamType):
    """Comma separated key=value parameter type."""

    name = "key=value,key=value"

    def convert(self, value, param, ctx):
        """Splits the values by comma and equal sign.

        Returns a dictionary build with key/value pairs.
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


class ClientOptionsParamType(CommaSeparatedKeyValueParamType):
    """Comma separated key=value parameter type for client options."""

    def __init__(self, client_options_type):
        """Instantiates ClientOptionsParamType for a client_options_type.

        Args:
            client_options_type (any): Pydantic model used for client options.
        """
        self.client_options_type = client_options_type

    def convert(self, value, param, ctx):
        """Splits the values by comma and equal sign.

        Returns an instance of client_options_type build with key/value pairs.
        """
        if isinstance(value, self.client_options_type):
            return value

        return self.client_options_type(**super().convert(value, param, ctx))


class HeadersParametersParamType(CommaSeparatedKeyValueParamType):
    """Comma separated key=value parameter type for headers parameters."""

    def __init__(self, headers_parameters_type):
        """Instantiates HeadersParametersParamType for a headers_paramters_type.

        Args:
            headers_parameters_type (any): Pydantic model used for headers parameters.
        """
        self.headers_parameters_type = headers_parameters_type

    def convert(self, value, param, ctx):
        """Splits the values by comma and equal sign.

        Returns an instance of headers_parameters_type build with key/value pairs.
        """
        if isinstance(value, self.headers_parameters_type):
            return value

        return self.headers_parameters_type(**super().convert(value, param, ctx))


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
@click.version_option(version=ralph_version)
def cli(verbosity=None):
    """Ralph is a stream-based tool to play with your logs."""
    configure_logging()
    if verbosity is not None:
        level = getattr(logging, verbosity, None)
        get_root_logger().setLevel(level)
        for handler in get_root_logger().handlers:
            handler.setLevel(level)


def backends_options(name=None, backend_types: List[BaseModel] = None):
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
                    elif field_type is CommaSeparatedTuple:
                        option_kwargs["type"] = CommaSeparatedTupleParamType()
                    elif isclass(field_type) and issubclass(field_type, ClientOptions):
                        option_kwargs["type"] = ClientOptionsParamType(field_type)
                    elif isclass(field_type) and issubclass(
                        field_type, HeadersParameters
                    ):
                        option_kwargs["type"] = HeadersParametersParamType(field_type)

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
    "-u",
    "--username",
    type=str,
    required=True,
    help="The user for which we generate credentials.",
)
@click.password_option(
    "-p",
    "--password",
    type=str,
    required=True,
    help="The password to encrypt for this user. Will be prompted if missing.",
)
@click.option(
    "-s",
    "--scope",
    type=str,
    required=True,
    multiple=True,
    default=[],
    help="The user scope(s). This option can be provided multiple times.",
)
@click.option(
    "-w",
    "--write",
    is_flag=True,
    default=False,
    help="Write new credentials to the LRS authentication file.",
)
def auth(username, password, scope, write):
    """Generate credentials for LRS HTTP basic authentification."""
    logger.info("Will generate credentials for user: %s", username)

    # Import required Pydantic models dynamically so that we don't create a
    # direct dependency between the CLI and the LRS
    # pylint: disable=invalid-name
    ServerUsersCredentials = import_string("ralph.api.auth.ServerUsersCredentials")
    UserCredentials = import_string("ralph.api.auth.UserCredentials")

    credentials = UserCredentials(
        username=username,
        hash=bcrypt.hashpw(
            bytes(password, encoding=settings.LOCALE_ENCODING), bcrypt.gensalt()
        ).decode("ascii"),
        scopes=scope,
    )

    if write:
        logger.info("Will append new credentials to: %s", settings.AUTH_FILE)

        # Force Path object instantiation so that the file creation can be
        # faked in a test environment.
        auth_file = Path(settings.AUTH_FILE)
        # Create the authentication file if it does not exist
        auth_file.parent.mkdir(parents=True, exist_ok=True)
        auth_file.touch()

        users = ServerUsersCredentials.parse_obj([])
        # Parse credentials file if not empty
        if auth_file.stat().st_size:
            users = ServerUsersCredentials.parse_file(auth_file)
        users += ServerUsersCredentials.parse_obj(
            [
                credentials,
            ]
        )
        auth_file.write_text(users.json(indent=2), encoding=settings.LOCALE_ENCODING)
        logger.info("User %s has been added to: %s", username, settings.AUTH_FILE)
    else:
        click.echo(
            (
                f"Copy/paste the following credentials to your LRS authentication "
                f"file located in: {settings.AUTH_FILE}\n"
                f"{credentials.json(indent=2)}"
            )
        )


@cli.command()
@click.option(
    "-p",
    "--parser",
    type=click.Choice([parser.lower() for parser, _ in settings.PARSERS]),
    required=True,
    help="Container format parser used to extract events",
)
def extract(parser):
    """Extract input events from a container format using a dedicated parser."""
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
    """Validate input events of given format."""
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
    """Convert input events to a given format."""
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
    "-t",
    "--target",
    type=str,
    default=None,
    help="Endpoint from which to fetch events (e.g. `/statements`)",
)
@click.option(
    "-q",
    "--query",
    type=JSONStringParamType(),
    default=None,
    help="Query object as a JSON string (database backends ONLY)",
)
def fetch(backend, archive, chunk_size, target, query, **options):
    """Fetch an archive or records from a configured backend."""
    logger.info(
        (
            "Fetching data from the configured %s backend "
            "(archive: %s | chunk size: %s | target: %s | query: %s)"
        ),
        backend,
        archive,
        chunk_size,
        target,
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
    elif backend_type == settings.BACKENDS.HTTP:
        for statement in backend.read(target=target, chunk_size=chunk_size):
            click.echo(
                bytes(
                    json.dumps(statement) if isinstance(statement, dict) else statement,
                    encoding="utf-8",
                )
            )
    elif backend_type is None:
        msg = "Cannot find an implemented backend type for backend %s"
        logger.error(msg, backend)
        raise UnsupportedBackendException(msg, backend)


# pylint: disable=unnecessary-direct-lambda-call, too-many-arguments
@click.argument("archive", required=False)
@backends_options(
    backend_types=[
        settings.BACKENDS.DATABASE,
        settings.BACKENDS.STORAGE,
        settings.BACKENDS.HTTP,
    ]
)
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
@click.option(
    "-t",
    "--target",
    type=str,
    default=None,
    help="Endpoint in which to push events (e.g. `statements`)",
)
def push(backend, archive, chunk_size, force, ignore_errors, target, **options):
    """Push an archive to a configured backend."""
    logger.info("Pushing archive %s to the configured %s backend", archive, backend)
    logger.debug("Backend parameters: %s", options)

    backend_type = get_backend_type(settings.BACKENDS, backend)
    backend = get_backend_instance(backend_type, backend, options)

    if backend_type == settings.BACKENDS.STORAGE:
        backend.write(sys.stdin.buffer, archive, overwrite=force)
    elif backend_type == settings.BACKENDS.DATABASE:
        backend.put(sys.stdin, chunk_size=chunk_size, ignore_errors=ignore_errors)
    elif backend_type == settings.BACKENDS.HTTP:
        backend.write(
            target=target,
            data=sys.stdin.buffer,
            chunk_size=chunk_size,
            ignore_errors=ignore_errors,
        )
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


@backends_options(name="runserver", backend_types=[settings.BACKENDS.DATABASE])
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
def runserver(backend: str, host: str, port: int, **options):
    """Run the API server for the development environment.

    Starts uvicorn programmatically for convenience and documentation.
    """
    logger.info("Running API server on %s:%s with %s backend", host, port, backend)
    logger.info(
        (
            "Do not use runserver in production - start production servers "
            "through a process manager such as gunicorn/supervisor/circus."
        )
    )

    # The LRS server relies only on environment and configuration variables for its
    # configuration (not CLI arguments). Therefore, we convert the CLI arguments to
    # environment variables by creating a temporary environment file and passing it to
    # uvicorn.
    with NamedTemporaryFile(mode="w", encoding=settings.LOCALE_ENCODING) as env_file:
        env_file.write(f"RALPH_RUNSERVER_BACKEND={backend}\n")
        for key, value in options.items():
            if value is None:
                continue
            backend_name, field_name = key.split(sep="_", maxsplit=1)
            key = f"RALPH_BACKENDS__DATABASE__{backend_name}__{field_name}".upper()
            if isinstance(value, tuple):
                value = ",".join(value)
            if issubclass(type(value), ClientOptions):
                for key_dict, value_dict in value.dict().items():
                    if value_dict is None:
                        continue
                    key_dict = f"{key}__{key_dict}"
                    logger.debug(
                        "Setting environment variable %s to '%s'", key_dict, value_dict
                    )
                    env_file.write(f"{key_dict}={value_dict}\n")
                continue
            logger.debug("Setting environment variable %s to '%s'", key, value)
            env_file.write(f"{key}={value}\n")
        env_file.seek(0)
        try:
            uvicorn.run(
                "ralph.api:app",
                env_file=env_file.name,
                host=host,
                port=port,
                log_level="debug",
                reload=True,
            )
        except NameError as err:  # pylint: disable=redefined-outer-name
            raise ModuleNotFoundError(
                "You need to install 'lrs' optional dependencies to use the runserver "
                "command: pip install ralph-malph[lrs]"
            ) from err

    logger.info("Shutting down uvicorn server.")
