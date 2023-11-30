"""FileSystem data backend for Ralph."""

import logging
import os
from datetime import datetime, timezone
from io import BufferedReader, IOBase
from pathlib import Path
from typing import Iterable, Iterator, Optional, Tuple, TypeVar, Union
from uuid import uuid4

from pydantic import PositiveInt

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
    Listable,
    Writable,
)
from ralph.backends.data.mixins import HistoryMixin
from ralph.conf import BaseSettingsConfig
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now, parse_iterable_to_dict

logger = logging.getLogger(__name__)


class FSDataBackendSettings(BaseDataBackendSettings):
    """FileSystem data backend default configuration.

    Attributes:
        DEFAULT_DIRECTORY_PATH (str or Path): The default target directory path where to
            perform list, read and write operations.
        DEFAULT_QUERY_STRING (str): The default query string to match files for the read
            operation.
        LOCALE_ENCODING (str): The encoding used for writing dictionaries to files.
        READ_CHUNK_SIZE (int): The default chunk size for reading files.
        WRITE_CHUNK_SIZE (int): The default chunk size for writing files.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__FS__"

    DEFAULT_DIRECTORY_PATH: Path = Path(".")
    DEFAULT_QUERY_STRING: str = "*"
    READ_CHUNK_SIZE: int = 4096
    WRITE_CHUNK_SIZE: int = 4096


Settings = TypeVar("Settings", bound=FSDataBackendSettings)


class FSDataBackend(
    BaseDataBackend[Settings, BaseQuery],
    Writable,
    Listable,
    HistoryMixin,
):
    """FileSystem data backend."""

    name = "fs"
    default_operation_type = BaseOperationType.CREATE
    unsupported_operation_types = {BaseOperationType.DELETE}

    def __init__(self, settings: Optional[Settings] = None):
        """Create the default target directory if it does not exist.

        Args:
            settings (FSDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self.settings = settings if settings else self.settings_class()
        self.default_directory = self.settings.DEFAULT_DIRECTORY_PATH
        self.default_query_string = self.settings.DEFAULT_QUERY_STRING

        if not self.default_directory.is_dir():
            msg = "Default directory doesn't exist, creating: %s"
            logger.info(msg, self.default_directory)
            self.default_directory.mkdir(parents=True)

        logger.debug("Default directory: %s", self.default_directory)

    def status(self) -> DataBackendStatus:
        """Check whether the default directory has appropriate permissions."""
        for mode in [os.R_OK, os.W_OK, os.X_OK]:
            if not os.access(self.default_directory, mode):
                logger.error(
                    "Invalid permissions for the default directory at %s. "
                    "The directory should have read, write and execute permissions.",
                    str(self.default_directory.absolute()),
                )
                return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def list(
        self, target: Optional[str] = None, details: bool = False, new: bool = False
    ) -> Union[Iterator[str], Iterator[dict]]:
        """List files and directories in the target directory.

        Args:
            target (str or None): The directory path where to list the files and
                directories.
                If target is `None`, the `default_directory` is used instead.
                If target is a relative path, it is considered to be relative to the
                    `default_directory_path`.
            details (bool): Get detailed file information instead of just file paths.
            new (bool): Given the history, list only not already read files.

        Yield:
            str: The next file path. (If details is False).
            dict: The next file details. (If details is True).

        Raise:
            BackendParameterException: If the `target` argument is not a directory path.
        """
        target: Path = Path(target) if target else self.default_directory
        if not target.is_absolute() and target != self.default_directory:
            target = self.default_directory / target
        try:
            paths = set(target.absolute().iterdir())
        except OSError as error:
            msg = "Invalid target argument"
            logger.error("%s. %s", msg, error)
            raise BackendParameterException(msg, error.strerror) from error

        logger.debug("Found %d files", len(paths))

        if new:
            paths -= set(map(Path, self.get_command_history(self.name, "read")))
            logger.debug("New files: %d", len(paths))

        if not details:
            for path in paths:
                yield str(path)

            return

        for path in paths:
            stats = path.stat()
            modified_at = datetime.fromtimestamp(int(stats.st_mtime), tz=timezone.utc)
            yield {
                "path": str(path),
                "size": stats.st_size,
                "modified_at": modified_at.isoformat(),
            }

    def read(  # noqa: PLR0913
        self,
        query: Optional[Union[str, BaseQuery]] = None,
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Optional[PositiveInt] = None,
    ) -> Union[Iterator[bytes], Iterator[dict]]:
        """Read files matching the query in the target folder and yield them.

        Args:
            query: (str or BaseQuery): The relative pattern for the files to read.
            target (str or None): The target directory path containing the files.
                If target is `None`, the `default_directory_path` is used instead.
                If target is a relative path, it is considered to be relative to the
                    `default_directory_path`.
            chunk_size (int or None): The chunk size when reading files.
                If `chunk_size` is `None` it defaults to `READ_CHUNK_SIZE`.
                If `raw_output` is set to `False`, files are read line by line.
            raw_output (bool): Controls whether to yield bytes or dictionaries.
            ignore_errors (bool): If `True`, encoding errors during the read operation
                will be ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            max_statements (int): The maximum number of statements to yield.
                If `None` (default) or `0`, there is no maximum.

        Yield:
            bytes: The next chunk of the read files if `raw_output` is True.
            dict: The next JSON parsed line of the read files if `raw_output` is False.

        Raise:
            BackendException: If a failure during the read operation occurs or
                during JSON encoding lines and `ignore_errors` is set to `False`.
        """
        yield from super().read(
            query, target, chunk_size, raw_output, ignore_errors, max_statements
        )

    def _read_bytes(
        self,
        query: BaseQuery,
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,  # noqa: ARG002
    ) -> Iterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        for file, path in self._iter_files_matching_query(target, query):
            while chunk := file.read(chunk_size):
                yield chunk
            # The file has been read, add a new entry to the history.
            self._append_to_history("read", path)

    def _read_dicts(
        self,
        query: BaseQuery,
        target: Optional[str],
        chunk_size: int,  # noqa: ARG002
        ignore_errors: bool,
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        for file, path in self._iter_files_matching_query(target, query):
            yield from parse_iterable_to_dict(file, ignore_errors)
            # The file has been read, add a new entry to the history.
            self._append_to_history("read", path)

    def _append_to_history(self, action: str, path: Path):
        """Append a new entry to the history."""
        self.append_to_history(
            {
                "backend": self.name,
                "action": action,
                # WARNING: previously only the file name was used as the ID
                # By changing this to the absolute file path, previously fetched
                # files will not be marked as read anymore.
                "id": str(path.absolute()),
                "filename": path.name,
                "size": path.stat().st_size,
                "timestamp": now(),
            }
        )

    def _iter_files_matching_query(
        self, target: Optional[str], query: BaseQuery
    ) -> Iterator[Tuple[BufferedReader, Path]]:
        """Return file/path tuples for files matching the query in the target folder."""
        if not query.query_string:
            query.query_string = self.default_query_string

        path = Path(target) if target else self.default_directory
        if not path.is_absolute() and path != self.default_directory:
            path = self.default_directory / path

        paths = list(filter(lambda x: x.is_file(), path.glob(query.query_string)))
        if not paths:
            msg = "No file found for query: %s"
            logger.info(msg, path / Path(str(query.query_string)))
            return

        logger.debug("Reading matching files: %s", paths)
        for path in paths:
            with path.open("rb") as file:
                yield file, path

    def write(  # noqa: PLR0913
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Optional[str] = None,
        chunk_size: Optional[int] = None,
        ignore_errors: bool = False,
        operation_type: Optional[BaseOperationType] = None,
    ) -> int:
        """Write data records to the target file and return their count.

        Args:
            data: (Iterable or IOBase): The data to write.
            target (str or None): The target file path.
                If target is a relative path, it is considered to be relative to the
                    `default_directory_path`.
                If target is `None`, a random (uuid4) file is created in the
                    `default_directory_path` and used as the target instead.
            chunk_size (int or None): Ignored.
            ignore_errors (bool): If `True`, errors during decoding and encoding of
                records are ignored and logged.
                If `False` (default), a `BackendException` is raised on any error.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If operation_type is `CREATE` or `INDEX`, the target file is expected to
                    be absent. If the target file exists a `FileExistsError` is raised.
                If operation_type is `UPDATE`, the target file is overwritten.
                If operation_type is `APPEND`, the data is appended to the
                    end of the target file.

        Return:
            int: The number of written files.

        Raise:
            BackendException: If any failure occurs during the write operation or
                if an inescapable failure occurs and `ignore_errors` is set to `True`.
                E.g.: the `operation_type` is `CREATE` or `INDEX` and the target file
                already exists.
            BackendParameterException: If the `operation_type` is `DELETE` as it is not
                supported.
        """
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def _write_dicts(  # noqa: PLR0913
        self,
        data: Iterable[dict],
        target: Optional[str],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        return super()._write_dicts(
            data, target, chunk_size, ignore_errors, operation_type
        )

    def _write_bytes(  # noqa: PLR0913
        self,
        data: Iterable[bytes],
        target: Optional[str],
        chunk_size: int,  # noqa: ARG002
        ignore_errors: bool,  # noqa: ARG002
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""
        if not target:
            target = f"{now()}-{uuid4()}"
            msg = "Target file not specified; using random file name: %s"
            logger.info(msg, target)

        path = Path(target)
        path = path if path.is_absolute() else self.default_directory / path

        if operation_type in [BaseOperationType.CREATE, BaseOperationType.INDEX]:
            if path.is_file():
                msg = (
                    "%s already exists and overwrite is not allowed with operation_type"
                    " create or index."
                )
                logger.error(msg, path)
                raise BackendException(msg % path)

            logger.debug("Creating file: %s", path)

        mode = "wb"
        if operation_type == BaseOperationType.APPEND:
            mode = "ab"
            logger.debug("Appending to file: %s", path)

        try:
            with path.open(mode) as file:
                for chunk in data:
                    file.write(chunk)
        except OSError as error:
            msg = "Failed to write to %s: %s"
            logger.error(msg, path, error)
            raise BackendException(msg % (path, error)) from error

        # The file has been created, add a new entry to the history.
        self.append_to_history(
            {
                "backend": self.name,
                "action": "write",
                # WARNING: previously only the file name was used as the ID
                # By changing this to the absolute file path, previously written
                # files will not be marked as written anymore.
                "id": str(path.absolute()),
                "filename": path.name,
                "size": path.stat().st_size,
                "timestamp": now(),
            }
        )
        logger.debug("Written %s with success", path.absolute())
        return 1

    def close(self) -> None:
        """FS backend has no open connections to close. No action."""
        logger.info("No open connections to close; skipping")
