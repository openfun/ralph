"""Ralph CLI entrypoint"""

import logging
import sys
from inspect import signature

import click
import click_log
from click_option_group import optgroup

from ralph.defaults import (
    AVAILABLE_PARSERS,
    AVAILABLE_STORAGE_BACKENDS,
    DEFAULT_GELF_PARSER_CHUNCK_SIZE,
    ENVVAR_PREFIX,
    Parsers,
    StorageBackends,
)
from ralph.utils import get_class_from_name, get_instance_from_class, get_root_logger

# cli module logger
logger = logging.getLogger(__name__)
click_log.basic_config(logger)


PARSERS = list(AVAILABLE_PARSERS)
STORAGE_BACKENDS = list(AVAILABLE_STORAGE_BACKENDS)


@click.group(name="ralph")
@click_log.simple_verbosity_option(get_root_logger())
def cli():
    """Ralph is a stream-based tool to play with your logs"""


def backends_options(name=None, backends=None):
    """Backend-related options decorator for Ralph commands"""

    def wrapper(command):
        command = (
            click.option(
                "-b",
                "--backend",
                type=click.Choice(backends),
                required=True,
                help="Storage backend",
            )
        )(command)

        for backend in backends:
            backend_class = get_class_from_name(backend, StorageBackends)

            for parameter in signature(backend_class.__init__).parameters.values():
                if parameter.name == "self":
                    continue
                option = f"--{backend_class.name}-{parameter.name}".replace("_", "-")
                envvar = (
                    f"{ENVVAR_PREFIX}_{backend_class.name}_{parameter.name}".upper()
                )
                command = (optgroup.option(option, envvar=envvar))(command)
            command = (optgroup.group(f"{backend_class.name} storage backend"))(command)

        command = (cli.command(name=name or command.__name__))(command)
        return command

    return wrapper


@cli.command()
@click.option(
    "-p",
    "--parser",
    type=click.Choice(PARSERS),
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

    parser = get_class_from_name(parser, Parsers)()

    for event in parser.parse(sys.stdin, chunksize=chunksize):
        click.echo(event)


@click.argument("archive")
@backends_options(backends=STORAGE_BACKENDS)
def fetch(backend, archive, **options):
    """Fetch an archive from a configured storage backend"""

    logger.info("Fetching archive %s from the configured %s backend", archive, backend)
    logger.debug("Backend parameters: %s", options)

    storage = get_instance_from_class(
        get_class_from_name(backend, StorageBackends), **options
    )
    storage.read(archive)


@backends_options(name="list", backends=STORAGE_BACKENDS)
def list_(backend, **options):
    """List available archives from a configured storage backend"""

    logger.info("Listing archives for the configured %s backend", backend)
    logger.debug("Backend parameters: %s", options)

    storage = get_instance_from_class(
        get_class_from_name(backend, StorageBackends), **options
    )
    archives = storage.list()
    if len(archives) == 0:
        logger.warning("Configured %s backend contains no archive", backend)
    else:
        click.echo("\n".join(archives))
