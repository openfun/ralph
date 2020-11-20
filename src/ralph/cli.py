"""Ralph CLI entrypoint"""

import json
import logging
import sys
from inspect import signature

import click
import click_log
from click_option_group import optgroup

from ralph.backends import BackendTypes
from ralph.defaults import (
    DEFAULT_BACKEND_CHUNCK_SIZE,
    DEFAULT_GELF_PARSER_CHUNCK_SIZE,
    ENVVAR_PREFIX,
    DatabaseBackends,
    Parsers,
    StorageBackends,
)
from ralph.exceptions import UnsupportedBackendException
from ralph.logger import configure_logging
from ralph.utils import (
    get_backend_type,
    get_class_from_name,
    get_class_names,
    get_instance_from_class,
    get_root_logger,
)

# cli module logger
logger = logging.getLogger(__name__)
click_log.basic_config(logger)

# Lazy evaluations
DATABASE_BACKENDS = (lambda: [backend.value for backend in DatabaseBackends])()
PARSERS = (lambda: [parser.value for parser in Parsers])()
STORAGE_BACKENDS = (lambda: [backend.value for backend in StorageBackends])()
BACKENDS = (lambda: DATABASE_BACKENDS + STORAGE_BACKENDS)()


@click.group(name="ralph")
@click_log.simple_verbosity_option(get_root_logger())
def cli():
    """Ralph is a stream-based tool to play with your logs"""

    configure_logging()


def backends_options(name=None, backends=None):
    """Backend-related options decorator for Ralph commands"""

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
                if isinstance(parameter.default, bool):
                    option = (
                        f"{option}/--no-{backend_class.name}-{parameter.name}".replace(
                            "_", "-"
                        )
                    )
                    option_kwargs["is_flag"] = True
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
@click.option(
    "-c",
    "--chunksize",
    type=int,
    default=DEFAULT_GELF_PARSER_CHUNCK_SIZE,
    help="Parse events by chunks of size #",
)
def extract(parser, chunksize):
    """Extract input events from a container format using a dedicated parser"""

    logger.info(
        "Extracting events using the %s parser (chunk size: %d)", parser, chunksize
    )

    parser = get_class_from_name(parser, PARSERS)()

    for event in parser.parse(sys.stdin, chunksize=chunksize):
        click.echo(event)


@click.argument("archive", required=False)
@backends_options(backends=BACKENDS)
@click.option(
    "-c",
    "--chunk-size",
    type=int,
    default=DEFAULT_BACKEND_CHUNCK_SIZE,
    help="Get events by chunks of size #",
)
def fetch(backend, archive, chunk_size, **options):
    """Fetch an archive or records from a configured backend"""

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
    default=DEFAULT_BACKEND_CHUNCK_SIZE,
    help="Get events by chunks of size #",
)
@click.option(
    "-f", "--force", default=False, is_flag=True, help="Overwrite existing archives"
)
def push(backend, archive, chunk_size, force, **options):
    """Push an archive to a configured backend"""

    logger.info("Pushing archive %s to the configured %s backend", archive, backend)
    logger.debug("Backend parameters: %s", options)

    backend_class = get_class_from_name(backend, BACKENDS)
    backend = get_instance_from_class(backend_class, **options)
    backend_type = get_backend_type(backend_class)

    if backend_type == BackendTypes.STORAGE:
        backend.write(archive, overwrite=force)
    elif backend_type == BackendTypes.DATABASE:
        backend.put(chunk_size=chunk_size)
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
    help="Get archives detailled output (JSON)",
)
def list_(details, new, backend, **options):
    """List available archives from a configured storage backend"""

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
