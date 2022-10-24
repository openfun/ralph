"""FileSystem data backend for Ralph."""

import json
import logging
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Generator, Iterable, Union
from uuid import uuid4

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
    enforce_query_checks,
)
from ralph.backends.mixins import HistoryMixin
from ralph.conf import BaseSettingsConfig, core_settings
from ralph.exceptions import BackendParameterException
from ralph.utils import now

logger = logging.getLogger(__name__)


class FileSystemDataBackendSettings(BaseDataBackendSettings):
    """Represent the FileSystem data backend default configuration."""

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__FS__"

    DEFAULT_DIRECTORY_PATH: str = str(core_settings.APP_DIR / "archives")
    DEFAULT_QUERY_STRING: str = "*"
    DEFAULT_CHUNK_SIZE: int = 4096


class FileSystemDataBackend(HistoryMixin, BaseDataBackend):
    """FileSystem data backend."""

    name = "fs"
    default_operation_type = BaseOperationType.CREATE
    settings = FileSystemDataBackendSettings()

    def __init__(
        self,
        default_directory_path: str = settings.DEFAULT_DIRECTORY_PATH,
        default_query_string: str = settings.DEFAULT_QUERY_STRING,
        default_chunk_size: int = settings.DEFAULT_CHUNK_SIZE,
    ):
        """Create the default target directory if it does not exist.

        Args:
            default_directory_path (str): The default target directory path where to
                perform list, read and write operations.
            default_query_string (str): The default query string to match files for the
                read operation.
            default_chunk_size (int): The default chunk size for reading files.
        """

        self.default_directory = Path(default_directory_path)
        self.default_query_string = default_query_string
        self.default_chunk_size = default_chunk_size

        if not self.default_directory.is_dir():
            msg = "Default directory doesn't exist, creating: %s"
            logger.info(msg, self.default_directory)
            self.default_directory.mkdir(parents=True)

        logger.debug("Default directory: %s", self.default_directory)

    def status(self) -> DataBackendStatus:
        """Check whether the default directory has appropriate write permissions."""

        if os.access(self.default_directory, os.W_OK):
            return DataBackendStatus.OK

        return DataBackendStatus.ERROR

    def list(
        self, target: str = None, details: bool = False, new: bool = False
    ) -> Generator[None, Union[str, dict], None]:
        """List files and directories contained in the target directory.

        Args:
            target (str or None): The directory path where to list the files.
                If target is `None`, the `default_directory_path` is used instead.
            details (bool): Get detailed file information instead of just file paths.
            new (bool): Given the history, list only not already read files.

        Yields:
            str: The next file path. (If details is False).
            dict: The next file details. (If details is True).
        """

        target = Path(target) if target else self.default_directory
        paths = [str(path) for path in target.iterdir()]

        logger.debug("Found %d files", len(paths))

        if new:
            paths = set(paths) - set(self.get_command_history(self.name, "fetch"))
            logger.debug("New files: %d", len(paths))

        if not details:
            for path in paths:
                yield path

            return

        for path in paths:
            path = Path(path)
            stats = path.stat()
            modified_at = datetime.fromtimestamp(int(stats.st_mtime), tz=timezone.utc)
            yield {
                "filename": path.name,
                "size": stats.st_size,
                "modified_at": modified_at.isoformat(),
            }

    @enforce_query_checks
    def read(
        self,
        *,
        query: Union[str, BaseQuery] = None,
        target: str = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
    ) -> Generator[None, Union[bytes, dict], None]:
        """Read files matching the query in the target folder and yield them.

        Args:
            query: (str or BaseQuery): The relative pattern for the files to read.
            target (str or None): The target directory path containing the files.
                If target is `None`, the `default_directory_path` is used instead.
            chunk_size (int or None): The chunk size for reading files.

        Yields:
            bytes: The next chunk of the read files if `raw_output` is True.
            dict: The next JSON parsed line of the read files if `raw_output` is False.
        """

        if not query.query_string:
            query.query_string = self.default_query_string

        if not chunk_size:
            chunk_size = self.default_chunk_size

        target = Path(target) if target else self.default_directory
        paths = list(target.glob(query.query_string))

        if not paths:
            logger.info("No file found for query: %s", target / query.query_string)
            return

        logger.debug("Reading matching files: %s", paths)

        for path in paths:
            with path.open("rb") as file:
                reader = self._read_raw if raw_output else self._read_dict
                for chunk in reader(file, chunk_size):
                    yield chunk

            # The file has been read, add a new entry to the history.
            self.append_to_history(
                {
                    "backend": self.name,
                    "command": "fetch",
                    # WARNING: previously only the file name was used as the ID
                    # By changing this to the full file path, previously fetched files
                    # will not be marked as read anymore.
                    "id": str(path),
                    "filename": path.name,
                    "size": path.stat().st_size,
                    "fetched_at": now(),
                }
            )

    def write(  # pylint: disable=too-many-arguments
        self,
        stream: Iterable[bytes],
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        ignore_errors: bool = False,
        operation_type: Union[BaseOperationType, None] = None,
    ) -> int:
        """Write stream records to the target file and return their count.

        Args:
            stream: (Iterable): The stream containing data to write.
            target (str or None): The target file path.
                If target is a relative path, it is considered to be relative to the
                    `default_directory_path`.
                If target is `None`, a random (uuid4) file is created in the
                    `default_directory_path` and used as the target instead.
            chunk_size (int or None): Ignored. Is equal to the stream chunk size.
            ignore_errors (bool): Ignored.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If operation_type is `CREATE` or `INDEX`, the target file is expected to
                    be absent. If the target file exists a `FileExistsError` is raised.
                If operation_type is `UPDATE`, the target file is overwritten.
                If operation_type is `APPEND`, the stream content is appended to the
                    end of the target file.

        Returns:
            int: The number of written files. (Always equal to 1).
        """

        if not operation_type:
            operation_type = self.default_operation_type

        if operation_type == BaseOperationType.DELETE:
            msg = "Delete operation_type is not allowed."
            logger.error(msg)
            raise BackendParameterException(msg)

        if not target:
            target = str(uuid4())
            logger.info("Target file not specified; using random file name: %s", target)

        target = Path(target)
        path = target if target.is_absolute() else self.default_directory / target

        if operation_type in [BaseOperationType.CREATE, BaseOperationType.INDEX]:
            if path.is_file():
                msg = (
                    "%s already exists and overwrite is not allowed with operation_type"
                    " create or index."
                )
                logger.error(msg, path)
                raise FileExistsError(msg % path)

            logger.debug("Creating file: %s", path)

        mode = "wb"
        if operation_type in [BaseOperationType.APPEND]:
            mode = "ab"
            logger.debug("Appending to file: %s", path)

        with path.open(mode) as file:
            for chunk in stream:
                file.write(chunk)

        # The file has been created, add a new entry to the history.
        self.append_to_history(
            {
                "backend": self.name,
                "command": "push",
                "id": str(path),
                "filename": path.name,
                "size": path.stat().st_size,
                "pushed_at": now(),
            }
        )
        return 1

    @staticmethod
    def _read_raw(file, chunk_size):
        """Read the `file` in chunks of size `chunk_size` and yield them."""

        while chunk := file.read(chunk_size):
            yield chunk

    @staticmethod
    def _read_dict(file, _chunk_size):
        """Read the `file` by line and yield JSON parsed dictionaries."""

        for i, line in enumerate(file):
            try:
                yield json.loads(line)
            except (TypeError, json.JSONDecodeError) as err:
                logger.error("Raised error: %s, in file %s at line %s", err, file, i)
