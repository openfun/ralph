"""FileSystem storage backend for Ralph"""

import datetime
import logging
from pathlib import Path

from ralph.conf import settings
from ralph.utils import now

from ..mixins import HistoryMixin
from .base import BaseStorage

logger = logging.getLogger(__name__)


class FSStorage(HistoryMixin, BaseStorage):
    """FileSystem storage backend."""

    name = "fs"

    def __init__(self, path: str = settings.BACKENDS.STORAGE.FS.PATH):
        """Creates the path directory if it does not exist."""

        self._path = Path(path)
        if not self._path.is_dir():
            logger.info("FS storage directory doesn't exist, creating: %s", self._path)
            self._path.mkdir(parents=True)

        logger.debug("File system storage path: %s", self._path)

    def _get_filepath(self, name, strict=False):
        """Returns path of the archive in the FS storage, or throws an exception if
        not found.
        """

        file_path = self._path / Path(name)
        if strict and not file_path.exists():
            msg = "%s file does not exist"
            logger.error(msg, file_path)
            raise FileNotFoundError(msg % file_path)
        return file_path

    def _details(self, name):
        """Gets `name` archive details."""

        file_path = self._get_filepath(name)
        stats = file_path.stat()

        return {
            "filename": name,
            "size": stats.st_size,
            "modified_at": datetime.datetime.fromtimestamp(
                int(stats.st_mtime), tz=datetime.timezone.utc
            ).isoformat(),
        }

    def list(self, details=False, new=False):
        """Lists files in the storage backend."""

        archives = [archive.name for archive in self._path.iterdir()]
        logger.debug("Found %d archives", len(archives))

        if new:
            archives = set(archives) - set(self.get_command_history(self.name, "fetch"))
            logger.debug("New archives: %d", len(archives))

        for archive in archives:
            yield self._details(archive) if details else archive

    def url(self, name):
        """Gets `name` file absolute URL."""

        return str(self._get_filepath(name).resolve(strict=True))

    def read(self, name, chunk_size: int = 4096):
        """Reads `name` file and yields its content by chunks of a given size."""

        logger.debug("Getting archive: %s", name)

        with self._get_filepath(name).open("rb") as file:
            while chunk := file.read(chunk_size):
                yield chunk

        details = self._details(name)
        # Archive is supposed to have been fully fetched, add a new entry to
        # the history.
        self.append_to_history(
            {
                "backend": self.name,
                "command": "fetch",
                "id": name,
                "filename": details.get("filename"),
                "size": details.get("size"),
                "fetched_at": now(),
            }
        )

    def write(self, stream, name, overwrite=False):
        """Writes content to the `name` target."""

        logger.debug("Creating archive: %s", name)

        file_path = self._get_filepath(name)
        if file_path.is_file() and not overwrite:
            msg = "%s already exists and overwrite is not allowed"
            logger.error(msg, name)
            raise FileExistsError(msg, name)

        with file_path.open("wb") as file:
            for chunk in stream:
                file.write(chunk)

        details = self._details(name)
        # Archive is supposed to have been fully created, add a new entry to
        # the history.
        self.append_to_history(
            {
                "backend": self.name,
                "command": "push",
                "id": name,
                "filename": details.get("filename"),
                "size": details.get("size"),
                "pushed_at": now(),
            }
        )
