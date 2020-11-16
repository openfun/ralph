"""FileSystem storage backend for Ralph"""

import datetime
import logging
import sys
from pathlib import Path

from ralph.defaults import FS_STORAGE_DEFAULT_PATH

from ..mixins import HistoryMixin
from .base import BaseStorage

logger = logging.getLogger(__name__)


class FSStorage(HistoryMixin, BaseStorage):
    """FileSystem storage backend"""

    name = "fs"

    def __init__(self, path=FS_STORAGE_DEFAULT_PATH):
        """Create the path directory if it does not exist"""

        self._path = Path(path)
        if not self._path.is_dir():
            logger.info("FS storage directory doesn't exist, creating: %s", self._path)
            self._path.mkdir(parents=True)

        logger.debug("File system storage path: %s", self._path)

    def _get_filepath(self, name, strict=False):
        """Return path of the archive in the FS storage, or throws an exception if not found"""

        file_path = self._path / Path(name)
        if strict and not file_path.exists():
            msg = "%s file does not exist"
            logger.error(msg, file_path)
            raise FileNotFoundError(msg % file_path)
        return file_path

    def _details(self, name):
        """Get name archive details"""

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
        """List files in the storage backend"""

        archives = [archive.name for archive in self._path.iterdir()]
        logger.debug("Found %d archives", len(archives))

        if new:
            archives = set(archives) - set(
                entry.get("id")
                for entry in filter(
                    lambda e: e["backend"] == self.name and e["command"] == "fetch",
                    self.history,
                )
            )

            logger.debug("New archives: %d", len(archives))

        for archive in archives:
            yield self._details(archive) if details else archive

    def url(self, name):
        """Get `name` file absolute URL"""

        return str(self._get_filepath(name).resolve(strict=True))

    def read(self, name, chunk_size=4096):
        """Read `name` file and stream its content by chunks of a given size"""

        logger.debug("Getting archive: %s", name)

        with self._get_filepath(name).open("rb") as file:
            while chunk := file.read(chunk_size):
                sys.stdout.buffer.write(chunk)

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
                "fetched_at": datetime.datetime.now(
                    tz=datetime.timezone.utc
                ).isoformat(),
            }
        )

    def write(self, name, chunk_size=4096, overwrite=False):
        """Write content to the `name` target"""

        logger.debug("Creating archive: %s", name)

        file_path = self._get_filepath(name)
        if file_path.is_file() and not overwrite:
            msg = "%s already exists and overwrite is not allowed"
            logger.error(msg, name)
            raise FileExistsError(msg, name)

        with file_path.open("w") as file:
            while chunk := sys.stdin.read(chunk_size):
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
                "pushed_at": datetime.datetime.now(
                    tz=datetime.timezone.utc
                ).isoformat(),
            }
        )
