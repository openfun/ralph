"""Ralph CLI entrypoint."""

import copy
import json
import logging
import re
import sys
from functools import partial, update_wrapper
from inspect import isasyncgen, isclass
from pathlib import Path
from tempfile import NamedTemporaryFile
from typing import Any, Callable, Optional, Type, Union

import bcrypt

try:
    import click
    from docstring_parser import parse
except ModuleNotFoundError as err:
    raise ModuleNotFoundError(
        "You need to install 'cli' optional dependencies to use the ralph "
        "command: pip install ralph-malph[cli]"
    ) from err
try:
    import uvicorn
except ModuleNotFoundError:
    # This error will be caught in the runserver command. We should be able to
    # use all commands except the runserver command when lrs optional
    # dependencies are not installed.
    pass
from click_option_group import optgroup
from pydantic import AnyUrl

from ralph import __version__ as ralph_version
from ralph.backends.data.base import (
    AsyncWritable,
    BaseAsyncDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackend,
    Writable,
)
from ralph.backends.loader import (
    get_cli_backends,
    get_cli_list_backends,
    get_cli_write_backends,
    get_lrs_backends,
)
from ralph.conf import ClientOptions, CommaSeparatedTuple, HeadersParameters, settings
from ralph.logger import configure_logging
from ralph.models.converter import Converter
from ralph.models.selector import ModelSelector
from ralph.models.validator import Validator
from ralph.utils import (
    execute_async,
    get_backend_instance,
    get_root_logger,
    import_string,
    iter_over_async,
)

# cli module logger
logger = logging.getLogger(__name__)


class CommaSeparatedTupleParamType(click.ParamType):
    """Comma-separated tuple parameter type."""

    name = "value1,value2,value3"

    def convert(self, value, param, ctx):
        """Split the value by comma to return a tuple of values."""
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
    """Comma-separated key=value parameter type."""

    name = "key=value,key=value"

    def convert(self, value, param, ctx):
        """Split the values by comma and equal sign.

        Return a dictionary build with key/value pairs.
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
    """Comma-separated key=value parameter type for client options."""

    def __init__(self, client_options_type: Any) -> None:
        """Instantiate ClientOptionsParamType for a client_options_type.

        Args:
            client_options_type (any): Pydantic model used for client options.
        """
        self.client_options_type = client_options_type

    def convert(self, value, param, ctx):
        """Split the values by comma and equal sign.

        Return an instance of client_options_type build with key/value pairs.
        """
        if isinstance(value, self.client_options_type):
            return value

        return self.client_options_type(**super().convert(value, param, ctx))


class HeadersParametersParamType(CommaSeparatedKeyValueParamType):
    """Comma-separated key=value parameter type for headers parameters."""

    def __init__(self, headers_parameters_type: Any) -> None:
        """Instantiate HeadersParametersParamType for a headers_parameters_type.

        Args:
            headers_parameters_type (any): Pydantic model used for headers parameters.
        """
        self.headers_parameters_type = headers_parameters_type

    def convert(self, value, param, ctx):
        """Split the values by comma and equal sign.

        Return an instance of headers_parameters_type build with key/value pairs.
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
                "You should provide a valid JSON string as input",
                param,
                ctx,
            )
        return options


class RalphBackendCLI(click.Group):
    """Ralph CLI entrypoint."""

    def __init__(
        self, *args, get_backends: Callable, method: Callable, **kwargs: Any
    ) -> None:
        """Initialize Ralph backend cli."""
        super().__init__(*args, **kwargs)
        self.get_backends = get_backends
        self.method = method
        self.method_click_params = self.method.__click_params__
        self.method_doc = self.method.__doc__

    def list_commands(self, ctx):
        """Register all sub-commands before calling `list_commands`."""
        for backend_class in self.get_backends().values():
            self.get_command(ctx, backend_class.name)
        return super().list_commands(ctx)

    def get_command(self, ctx, cmd_name) -> Union[click.Command, None]:
        """Register sub-command before calling `get_command`."""
        command = super().get_command(ctx, cmd_name)
        if command:
            return command

        backend_class = self.get_backends().get(cmd_name)
        if backend_class and ctx.command.name:
            self.add_backend_sub_command(backend_class, ctx.command.name)
            return super().get_command(ctx, cmd_name)

        return command

    def add_backend_read_options(
        self, backend_class: Type[DataBackend], method_params: dict
    ) -> None:
        """Add backend-related options for the `read` command."""
        prefetch = method_params.get("prefetch")
        if prefetch:
            self.method = click.option(
                "-p",
                "--prefetch",
                type=int,
                default=None,
                help=prefetch,
            )(self.method)

        query_help = method_params.get("query")
        if query_help:
            if issubclass(backend_class.query_class, BaseQuery):
                query_doc = [
                    f"  {param.arg_name} ({param.type_name}): {param.description}\n"
                    for param in parse(str(backend_class.query_class.__doc__)).params
                ]
                query_doc = "\n".join(query_doc)
                query_help = f"{query_help}\n\nQUERY Attributes:\n\n{query_doc}"

            if self.method.__doc__:
                self.method.__doc__ += f"\n\nQUERY: {query_help}"

    def add_backend_write_options(
        self, backend_class: Type[DataBackend], method_params: dict
    ) -> None:
        """Add backend-related options for the `write` command."""
        if not issubclass(backend_class, (Writable, AsyncWritable)):
            return

        operation_type = method_params.get("operation_type")
        if operation_type:
            choices = [
                op_type.value
                for op_type in BaseOperationType
                if op_type.value not in backend_class.unsupported_operation_types
            ]
            self.method = click.option(
                "-o",
                "--operation-type",
                type=click.Choice(choices),
                metavar="OP_TYPE",
                required=False,
                show_default=True,
                default=backend_class.default_operation_type.value,
                help=operation_type,
            )(self.method)

        if method_params.get("concurrency"):
            self.method = click.option(
                "-c",
                "--concurrency",
                type=int,
                default=1,
                help=method_params.get("concurrency"),
            )(self.method)

    def add_backend_settings_options(
        self, backend_settings: BaseDataBackendSettings
    ) -> Callable:
        """Add backend-related options from backend settings."""
        settings_params = {
            param.arg_name.lower().replace("_", "-"): param.description
            for param in parse(str(backend_settings.__doc__)).params
        }
        fields = backend_settings.__fields__.items()
        for name, field in sorted(fields, key=lambda x: x[0], reverse=True):
            if name in ["WRITE_CHUNK_SIZE", "READ_CHUNK_SIZE"]:
                continue
            field_name = name.lower().replace("_", "-")
            field_type = field.type_
            option = f"--{field_name}"
            option_kwargs = {
                "show_default": True,
                "default": getattr(backend_settings, name, None),
                "required": field.required,
                "help": settings_params.get(field_name),
            }
            if field.default:
                option_kwargs["type"] = type(field.default)
            # If the field is a boolean, convert it to a flag option
            if field_type is bool:
                option = f"{option}/--no-{field_name}"
                option_kwargs["is_flag"] = True
            elif field_type is dict:
                option_kwargs["type"] = CommaSeparatedKeyValueParamType()
            elif field_type is CommaSeparatedTuple:
                option_kwargs["type"] = CommaSeparatedTupleParamType()
            elif isclass(field_type):
                if issubclass(field_type, ClientOptions):
                    option_kwargs["type"] = ClientOptionsParamType(field_type)
                elif issubclass(field_type, HeadersParameters):
                    option_kwargs["type"] = HeadersParametersParamType(field_type)
                elif issubclass(field_type, AnyUrl):
                    option_kwargs["type"] = str
                elif field_type is Path:
                    option_kwargs["type"] = click.Path()

            self.method = click.option(option.lower(), **option_kwargs)(self.method)

    def add_backend_sub_command(
        self, backend_class: Type[DataBackend], command_name: str
    ) -> None:
        """Backend-related options decorator for Ralph commands."""
        self.method.__doc__ = copy.copy(self.method_doc)
        self.method.__click_params__ = copy.deepcopy(self.method_click_params)
        method = getattr(backend_class, command_name, self.method)
        method_docstring = parse(str(method.__doc__))
        method_params = {
            param.arg_name: param.description for param in method_docstring.params
        }
        backend_settings = backend_class.settings_class()
        for click_param in self.method.__click_params__:
            click_param.help = method_params.get(click_param.name)
            if click_param.name == "chunk_size":
                if command_name == "write":
                    click_param.default = backend_settings.WRITE_CHUNK_SIZE
                    click_param.show_default = True
                elif command_name == "read":
                    click_param.default = backend_settings.READ_CHUNK_SIZE
                    click_param.show_default = True

        self.method.__doc__ = (
            f"{backend_class.__doc__}\n\n{method_docstring.short_description}"
        )
        self.add_backend_read_options(backend_class, method_params)
        self.add_backend_write_options(backend_class, method_params)
        self.add_backend_settings_options(backend_settings)
        command = update_wrapper(partial(self.method, backend_class), self.method)
        self.add_command(click.command(name=backend_class.name)(command))


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
def cli(verbosity: Optional[str] = None):
    """The cli is a stream-based tool to play with your logs.

    It offers functionalities to:
    - Validate or convert learning data in different standards
    - Read and write learning data to various databases or servers
    - Manage an instance of a Ralph LRS server
    """
    configure_logging()
    if verbosity is not None:
        level = getattr(logging, verbosity)
        get_root_logger().setLevel(level)
        for handler in get_root_logger().handlers:
            handler.setLevel(level)


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
    "-M",
    "--agent-ifi-mbox",
    type=str,
    required=False,
    help="The mbox Inverse Functional Identifier of the associated agent.",
)
@click.option(
    "-S",
    "--agent-ifi-mbox-sha1sum",
    type=str,
    required=False,
    help="The mbox-sha1sum Inverse Functional Identifier of the associated agent.",
)
@click.option(
    "-O",
    "--agent-ifi-openid",
    type=str,
    required=False,
    help="The openid Inverse Functional Identifier of the associated agent.",
)
@click.option(
    "-A",
    "--agent-ifi-account",
    type=str,
    nargs=2,
    required=False,
    help=(
        'Input "{name} {homePage}". The account Inverse Functional Identifier of the '
        "associated agent."
    ),
)
@click.option(
    "-N",
    "--agent-name",
    type=str,
    required=False,
    help="The name of the associated agent.",
)
@click.option(
    "-w",
    "--write-to-disk",
    is_flag=True,
    default=False,
    help="Write new credentials to the LRS authentication file.",
)
def auth(  # noqa: PLR0913
    username,
    password,
    scope,
    write_to_disk,
    agent_ifi_mbox,
    agent_ifi_mbox_sha1sum,
    agent_ifi_openid,
    agent_ifi_account,
    agent_name,
):
    """Generate credentials for LRS HTTP basic authentication."""
    logger.info("Will generate credentials for user: %s", username)

    # Verify that exactly one agent representation has been provided
    if (
        sum(
            opt is not None
            for opt in [
                agent_ifi_mbox,
                agent_ifi_mbox_sha1sum,
                agent_ifi_openid,
                agent_ifi_account,
            ]
        )
        != 1
    ):
        raise click.UsageError(
            "Exactly one (1) of the ifi options is required. These options are:\n"
            "-M --agent-ifi-mbox : mbox Agent IFI\n"
            "-S --agent-ifi-mboxsha1sum : mbox-sha1sum Agent IFIr\n"
            "-O --agent-ifi-openid : openid Agent IFI\n"
            "-A --agent-ifi-account : account Agent IFI"
        )

    # Import required Pydantic models dynamically so that we don't create a
    # direct dependency between the CLI and the LRS

    ServerUsersCredentials = import_string(
        "ralph.api.auth.basic.ServerUsersCredentials"
    )
    UserCredentialsBasicAuth = import_string("ralph.api.auth.basic.UserCredentials")

    # NB: renaming classes below for clarity
    Account = import_string("ralph.models.xapi.base.ifi.BaseXapiAccount")
    AgentMbox = import_string("ralph.models.xapi.base.agents.BaseXapiAgentWithMbox")
    AgentMboxSha1sum = import_string(
        "ralph.models.xapi.base.agents.BaseXapiAgentWithMboxSha1Sum"
    )
    AgentOpenid = import_string("ralph.models.xapi.base.agents.BaseXapiAgentWithOpenId")
    AgentAccount = import_string(
        "ralph.models.xapi.base.agents.BaseXapiAgentWithAccount"
    )

    if agent_ifi_mbox:
        if agent_ifi_mbox[:7] != "mailto:":
            raise click.UsageError(
                'Mbox field must start with "mailto:" (e.g.: "mailto:foo@bar.com")'
            )
        agent = AgentMbox(mbox=agent_ifi_mbox, name=agent_name, objectType="Agent")
    if agent_ifi_mbox_sha1sum:
        agent = AgentMboxSha1sum(
            mbox_sha1sum=agent_ifi_mbox_sha1sum, name=agent_name, objectType="Agent"
        )
    if agent_ifi_openid:
        agent = AgentOpenid(
            openid=agent_ifi_openid, name=agent_name, objectType="Agent"
        )
    if agent_ifi_account:
        # Parse account details
        account = Account(homePage=agent_ifi_account[1], name=agent_ifi_account[0])
        agent = AgentAccount(account=account, name=agent_name, objectType="Agent")

    credentials = UserCredentialsBasicAuth(
        username=username,
        hash=bcrypt.hashpw(
            bytes(password, encoding=settings.LOCALE_ENCODING), bcrypt.gensalt()
        ).decode("ascii"),
        scopes=scope,
        agent=agent,
    )

    if write_to_disk:
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


@click.argument("query", required=False)
@click.option("-m", "--max-statements", type=int, default=None)
@click.option("-I", "--ignore-errors", is_flag=True, default=False)
@click.option("-s", "--chunk-size", type=int, default=None)
@click.option("-t", "--target", type=str, default=None)
def _read(  # noqa: PLR0913
    backend_class: Type[DataBackend],
    query: str,
    target: str,
    chunk_size: int,
    ignore_errors: bool,
    max_statements: int,
    prefetch: Optional[int] = None,
    **options,
):
    """Read records matching the QUERY (json or string) from a configured backend."""
    logger.info("Reading data from %s backend", backend_class.name)
    msg = (
        "(query: %s | target: %s | chunk size: %s  | ignore errors: %s | "
        "max statements: %s | prefetch: %s)"
    )
    logger.info(msg, query, target, chunk_size, ignore_errors, max_statements, prefetch)
    logger.debug("Backend parameters: %s", options)

    backend = get_backend_instance(backend_class, options)

    if query and issubclass(backend.query_class, BaseQuery):
        query: BaseQuery = backend.query_class.from_string(query)

    async_options = {}
    if isinstance(backend, BaseAsyncDataBackend):
        async_options["prefetch"] = prefetch

    statements = backend.read(
        query=query,
        target=target,
        chunk_size=chunk_size,
        raw_output=True,
        ignore_errors=ignore_errors,
        max_statements=max_statements,
        **async_options,
    )
    if isinstance(backend, BaseAsyncDataBackend):
        statements = iter_over_async(statements)

    for statement in statements:
        click.echo(statement, nl=False)


@cli.group(
    cls=RalphBackendCLI,
    get_backends=get_cli_backends,
    method=_read,
    options_metavar="",
    subcommand_metavar="BACKEND [OPTIONS] [QUERY]",
)
def read():
    """Read records matching the QUERY (json or string) from a configured backend."""


@click.option("-I", "--ignore-errors", is_flag=True, default=False)
@click.option("-s", "--chunk-size", type=int, default=None)
@click.option("-t", "--target", type=str, default=None)
def _write(  # noqa: PLR0913
    backend_class: Type[DataBackend],
    target: str,
    chunk_size: int,
    ignore_errors: bool,
    operation_type: str,
    concurrency: Optional[int] = None,
    **options,
):
    """Write an archive to a configured backend."""
    logger.info(
        "Writing to target %s for the configured %s backend", target, backend_class.name
    )
    logger.debug("Backend parameters: %s", options)
    backend = get_backend_instance(backend_class, options)

    writer = backend.write
    async_options = {}
    if isinstance(backend, AsyncWritable):
        writer = execute_async(backend.write)
        async_options = {"concurrency": concurrency}

    writer(
        data=sys.stdin.buffer,
        target=target,
        chunk_size=chunk_size,
        ignore_errors=ignore_errors,
        operation_type=BaseOperationType(operation_type) if operation_type else None,
        **async_options,
    )


@cli.group(
    cls=RalphBackendCLI,
    get_backends=get_cli_write_backends,
    method=_write,
    options_metavar="",
    subcommand_metavar="BACKEND [OPTIONS]",
)
def write():
    """Write data to a configured backend."""


@click.option("-n/-a", "--new/--all", default=False)
@click.option("-D/-I", "--details/--ids", default=False)
@click.option("-t", "--target", type=str, default=None)
def _list(
    backend_class: Type[DataBackend], target: str, details: bool, new: bool, **options
):
    """List available documents from a configured data backend."""
    logger.info("Listing documents for the configured %s backend", backend_class.name)
    logger.debug("Target container: %s", target)
    logger.debug("Fetch details: %s", str(details))
    logger.debug("Backend parameters: %s", options)

    backend = get_backend_instance(backend_class, options)
    documents = backend.list(target=target, details=details, new=new)
    documents = iter_over_async(documents) if isasyncgen(documents) else documents
    counter = 0
    for document in documents:
        click.echo(json.dumps(document) if details else document)
        counter += 1

    if counter == 0:
        logger.warning("Configured %s backend contains no document", backend.name)


@cli.group(
    cls=RalphBackendCLI,
    get_backends=get_cli_list_backends,
    method=_list,
    options_metavar="",
    subcommand_metavar="BACKEND [OPTIONS]",
    name="list",
)
def list_():
    """List available documents from a configured data backend."""


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
def _runserver(backend_class: Type[DataBackend], host: str, port: int, **options):
    """Run the API server for the development environment.

    Starts uvicorn programmatically for convenience and documentation.
    """
    logger.info(
        "Running API server on %s:%s with %s backend", host, port, backend_class.name
    )
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
        env_file.write(f"RALPH_RUNSERVER_BACKEND={backend_class.name}\n")
        for option, value in options.items():
            if value is None:
                continue

            key = f"RALPH_BACKENDS__LRS__{backend_class.name}__{option}".upper()
            if isinstance(value, tuple):
                value = ",".join(value)  # noqa: PLW2901

            if isinstance(value, ClientOptions):
                for key_dict, value_dict in value.dict().items():
                    if value_dict is None:
                        continue

                    key_dict = f"{key}__{key_dict}"  # noqa: PLW2901
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
        except NameError as error:
            raise ModuleNotFoundError(
                "You need to install 'lrs' optional dependencies to use the runserver "
                "command: pip install ralph-malph[lrs]"
            ) from error

    logger.info("Shutting down uvicorn server.")


@cli.group(
    cls=RalphBackendCLI,
    get_backends=get_lrs_backends,
    method=_runserver,
    options_metavar="",
    subcommand_metavar="BACKEND [OPTIONS]",
)
def runserver():
    """Run the API server for the development environment.

    Start uvicorn programmatically for convenience and documentation.
    """
