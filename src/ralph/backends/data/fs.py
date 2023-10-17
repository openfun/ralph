"""FileSystem data backend for Ralph."""

import logging
import os
from datetime import datetime, timezone
from io import BufferedReader, IOBase
from pathlib import Path
from typing import Iterable, Iterator, Tuple, Union
from uuid import uuid4

from ralph.backends.data.base import (
    BaseDataBackend,
    BaseDataBackendSettings,
    BaseOperationType,
    BaseQuery,
    DataBackendStatus,
)
from ralph.backends.mixins import HistoryMixin
from ralph.conf import BaseSettingsConfig
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now, parse_bytes_to_dict, parse_dict_to_bytes

logger = logging.getLogger(__name__)


class FSDataBackendSettings(BaseDataBackendSettings):
    """FileSystem data backend default configuration.

    Attributes:
        DEFAULT_CHUNK_SIZE (int): The default chunk size for reading files.
        DEFAULT_DIRECTORY_PATH (str or Path): The default target directory path where to
            perform list, read and write operations.
        DEFAULT_QUERY_STRING (str): The default query string to match files for the read
            operation.
        LOCALE_ENCODING (str): The encoding used for writing dictionaries to files.
    """

    class Config(BaseSettingsConfig):
        """Pydantic Configuration."""

        env_prefix = "RALPH_BACKENDS__DATA__FS__"

    DEFAULT_CHUNK_SIZE: int = 4096
    DEFAULT_DIRECTORY_PATH: Path = Path(".")
    DEFAULT_QUERY_STRING: str = "*"


class FSDataBackend(HistoryMixin, BaseDataBackend):
    """FileSystem data backend."""

    name = "fs"
    unsupported_operation_types = {BaseOperationType.DELETE}
    logger = logger
    query_class = BaseQuery
    settings_class = FSDataBackendSettings
    settings: settings_class

    def __init__(self, settings: Union[settings_class, None] = None):
        """Create the default target directory if it does not exist.

        Args:
            settings (FSDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self.default_directory = self.settings.DEFAULT_DIRECTORY_PATH
        self.default_query_string = self.settings.DEFAULT_QUERY_STRING

        if not self.default_directory.is_dir():
            msg = "Default directory doesn't exist, creating: %s"
            self.logger.info(msg, self.default_directory)
            self.default_directory.mkdir(parents=True)

        self.logger.debug("Default directory: %s", self.default_directory)

    def status(self) -> DataBackendStatus:
        """Check whether the default directory has appropriate permissions."""
        for mode in [os.R_OK, os.W_OK, os.X_OK]:
            if not os.access(self.default_directory, mode):
                self.logger.error(
                    "Invalid permissions for the default directory at %s. "
                    "The directory should have read, write and execute permissions.",
                    str(self.default_directory.absolute()),
                )
                return DataBackendStatus.ERROR

        return DataBackendStatus.OK

    def list(
        self, target: Union[str, None] = None, details: bool = False, new: bool = False
    ) -> Iterator[Union[str, dict]]:
        """List files and directories in the target directory.

        Args:
            target (str or None): The directory path where to list the files and
                directories.
                If target is `None`, the `default_directory` is used instead.
                If target is a relative path, it is considered to be relative to the
                    `default_directory_path`.
            details (bool): Get detailed file information instead of just file paths.
            new (bool): Given the history, list only not already read files.

        Yields:
            str: The next file path. (If details is False).
            dict: The next file details. (If details is True).

        Raises:
            BackendParameterException: If the `target` argument is not a directory path.
        """
        path = Path(target) if target else self.default_directory
        if not path.is_absolute() and path != self.default_directory:
            path = self.default_directory / path
        try:
            paths = set(path.absolute().iterdir())
        except OSError as error:
            msg = "Invalid target argument"
            self.logger.error("%s. %s", msg, error)
            raise BackendParameterException(msg, error.strerror) from error

        self.logger.debug("Found %d files", len(paths))

        if new:
            paths -= set(map(Path, self.get_command_history(self.name, "read")))
            self.logger.debug("New files: %d", len(paths))

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

    def read(
        self,
        query: Union[str, dict, query_class, None] = None,
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
        max_statements: Union[int, None] = None,
    ) -> Iterator[Union[bytes, dict]]:
        # pylint: disable=too-many-arguments
        """Read files matching the query in the target folder and yield them.

        Args:
            query: (str or BaseQuery): The relative pattern for the files to read.
            target (str or None): The target directory path containing the files.
                If target is `None`, the `default_directory_path` is used instead.
                If target is a relative path, it is considered to be relative to the
                    `default_directory_path`.
            chunk_size (int or None): The chunk size when reading documents by batches.
                Ignored if `raw_output` is set to False.
            raw_output (bool): Controls whether to yield bytes or dictionaries.
            ignore_errors (bool): If `True`, errors during the read operation
                will be ignored and logged. If `False` (default), a `BackendException`
                will be raised if an error occurs.
            max_statements: The maximum number of statements or chunks to yield.

        Yields:
            bytes: The next chunk of the read files if `raw_output` is True.
            dict: The next JSON parsed line of the read files if `raw_output` is False.

        Raises:
            BackendException: If a failure during the read operation occurs and
                `ignore_errors` is set to `False`.
        """
        yield from super().read(
            query, target, chunk_size, raw_output, ignore_errors, max_statements
        )

    def write(  # pylint: disable=too-many-arguments,useless-parent-delegation
        self,
        data: Union[IOBase, Iterable[bytes], Iterable[dict]],
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        ignore_errors: bool = False,
        operation_type: Union[BaseOperationType, None] = None,
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
            ignore_errors (bool): Ignored.
            operation_type (BaseOperationType or None): The mode of the write operation.
                If operation_type is `CREATE` or `INDEX`, the target file is expected to
                    be absent. If the target file exists a `FileExistsError` is raised.
                If operation_type is `UPDATE`, the target file is overwritten.
                If operation_type is `APPEND`, the data is appended to the
                    end of the target file.

        Returns:
            int: The number of written files.

        Raises:
            BackendException: If the `operation_type` is `CREATE` or `INDEX` and the
                target file already exists.
            BackendParameterException: If the `operation_type` is `DELETE` as it is not
                supported.
        """
        return super().write(data, target, chunk_size, ignore_errors, operation_type)

    def close(self) -> None:
        """FS backend has nothing to close, this method is not implemented."""
        msg = "FS data backend does not support `close` method"
        self.logger.error(msg)
        raise NotImplementedError(msg)

    def _read_bytes(
        self,
        query: query_class,
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
    ) -> Iterator[bytes]:
        """Method called by `self.read` yielding bytes. See `self.read`."""
        for file, path in self._iter_files_matching_query(target, query):
            while chunk := file.read(chunk_size):
                yield chunk

            self._append_to_history("read", path)

    def _read_dicts(
        self,
        query: query_class,
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
    ) -> Iterator[dict]:
        """Method called by `self.read` yielding dictionaries. See `self.read`."""
        for file, path in self._iter_files_matching_query(target, query):
            yield from parse_bytes_to_dict(file, ignore_errors, self.logger)
            self._append_to_history("read", path)

    def _write_bytes(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[bytes],
        target: Union[str, None],
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing bytes. See `self.write`."""
        if not target:
            target = f"{now()}-{uuid4()}"
            msg = "Target file not specified; using random file name: %s"
            self.logger.info(msg, target)

        path = Path(target)
        path = path if path.is_absolute() else self.default_directory / path
        if operation_type in [BaseOperationType.CREATE, BaseOperationType.INDEX]:
            if path.is_file():
                msg = (
                    "%s already exists and overwrite is not allowed with operation_type"
                    " create or index."
                )
                self.logger.error(msg, path)
                raise BackendException(msg % path)

            self.logger.debug("Creating file: %s", path)

        mode = "wb"
        if operation_type == BaseOperationType.APPEND:
            mode = "ab"
            self.logger.debug("Appending to file: %s", path)

        with path.open(mode) as file:
            for chunk in data:
                file.write(chunk)

        self._append_to_history("write", path)
        return 1

    def _write_dicts(  # pylint: disable=too-many-arguments
        self,
        data: Iterable[dict],
        target: Path,
        chunk_size: int,
        ignore_errors: bool,
        operation_type: BaseOperationType,
    ) -> int:
        """Method called by `self.write` writing dictionaries. See `self.write`."""
        bytes_data = parse_dict_to_bytes(
            data, self.settings.LOCALE_ENCODING, ignore_errors, self.logger
        )
        return self._write_bytes(
            bytes_data, target, chunk_size, ignore_errors, operation_type
        )

    def _iter_files_matching_query(
        self, target: Union[str, None], query: query_class
    ) -> Iterator[Tuple[BufferedReader, Path]]:
        """Return file/path tuples for files matching the query."""
        if not query.query_string:
            query.query_string = self.default_query_string

        path = Path(target) if target else self.default_directory
        if not path.is_absolute() and path != self.default_directory:
            path = self.default_directory / path

        paths = list(filter(lambda x: x.is_file(), path.glob(str(query.query_string))))
        if not paths:
            msg = "No file found for query: %s"
            self.logger.info(msg, path / Path(str(query.query_string)))
            return

        self.logger.debug("Reading matching files: %s", paths)
        for path in paths:
            with path.open("rb") as file:
                yield file, path

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
