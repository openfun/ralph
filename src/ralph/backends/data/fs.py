"""FileSystem data backend for Ralph."""

import json
import logging
import os
from datetime import datetime, timezone
from io import IOBase
from itertools import chain
from pathlib import Path
from typing import IO, Iterable, Iterator, Union
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
from ralph.conf import BaseSettingsConfig
from ralph.exceptions import BackendException, BackendParameterException
from ralph.utils import now

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
    default_operation_type = BaseOperationType.CREATE
    settings_class = FSDataBackendSettings
    settings: settings_class

    def __init__(self, settings: Union[settings_class, None] = None):
        """Create the default target directory if it does not exist.

        Args:
            settings (FSDataBackendSettings or None): The data backend settings.
                If `settings` is `None`, a default settings instance is used instead.
        """
        super().__init__(settings)
        self.default_chunk_size = self.settings.DEFAULT_CHUNK_SIZE
        self.default_directory = self.settings.DEFAULT_DIRECTORY_PATH
        self.default_query_string = self.settings.DEFAULT_QUERY_STRING
        self.locale_encoding = self.settings.LOCALE_ENCODING

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
        target = Path(target) if target else self.default_directory
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

    @enforce_query_checks
    def read(
        self,
        *,
        query: Union[str, BaseQuery] = None,
        target: Union[str, None] = None,
        chunk_size: Union[int, None] = None,
        raw_output: bool = False,
        ignore_errors: bool = False,
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

        Yields:
            bytes: The next chunk of the read files if `raw_output` is True.
            dict: The next JSON parsed line of the read files if `raw_output` is False.

        Raises:
            BackendException: If a failure during the read operation occurs and
                `ignore_errors` is set to `False`.
        """
        if not query.query_string:
            query.query_string = self.default_query_string

        if not chunk_size:
            chunk_size = self.default_chunk_size

        target = Path(target) if target else self.default_directory
        if not target.is_absolute() and target != self.default_directory:
            target = self.default_directory / target
        paths = list(
            filter(lambda path: path.is_file(), target.glob(query.query_string))
        )

        if not paths:
            logger.info("No file found for query: %s", target / query.query_string)
            return

        logger.debug("Reading matching files: %s", paths)

        for path in paths:
            with path.open("rb") as file:
                reader = self._read_raw if raw_output else self._read_dict
                for chunk in reader(file, chunk_size, ignore_errors):
                    yield chunk

            # The file has been read, add a new entry to the history.
            self.append_to_history(
                {
                    "backend": self.name,
                    "action": "read",
                    # WARNING: previously only the file name was used as the ID
                    # By changing this to the absolute file path, previously fetched
                    # files will not be marked as read anymore.
                    "id": str(path.absolute()),
                    "filename": path.name,
                    "size": path.stat().st_size,
                    "timestamp": now(),
                }
            )

    def write(  # pylint: disable=too-many-arguments
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
        data = iter(data)
        try:
            first_record = next(data)
        except StopIteration:
            logger.info("Data Iterator is empty; skipping write to target.")
            return 0
        if not operation_type:
            operation_type = self.default_operation_type

        if operation_type == BaseOperationType.DELETE:
            msg = "Delete operation_type is not allowed."
            logger.error(msg)
            raise BackendParameterException(msg)

        if not target:
            target = f"{now()}-{uuid4()}"
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
                raise BackendException(msg % path)

            logger.debug("Creating file: %s", path)

        mode = "wb"
        if operation_type == BaseOperationType.APPEND:
            mode = "ab"
            logger.debug("Appending to file: %s", path)

        with path.open(mode) as file:
            is_dict = isinstance(first_record, dict)
            writer = self._write_dict if is_dict else self._write_raw
            for chunk in chain((first_record,), data):
                writer(file, chunk)

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
        return 1

    def close(self) -> None:
        """FS backend has nothing to close, this method is not implemented."""
        msg = "FS data backend does not support `close` method"
        logger.error(msg)
        raise NotImplementedError(msg)

    @staticmethod
    def _read_raw(file: IO, chunk_size: int, _ignore_errors: bool) -> Iterator[bytes]:
        """Read the `file` in chunks of size `chunk_size` and yield them."""
        while chunk := file.read(chunk_size):
            yield chunk

    @staticmethod
    def _read_dict(file: IO, _chunk_size: int, ignore_errors: bool) -> Iterator[dict]:
        """Read the `file` by line and yield JSON parsed dictionaries."""
        for i, line in enumerate(file):
            try:
                yield json.loads(line)
            except (TypeError, json.JSONDecodeError) as err:
                msg = "Raised error: %s, in file %s at line %s"
                logger.error(msg, err, file, i)
                if not ignore_errors:
                    raise BackendException(msg % (err, file, i)) from err

    @staticmethod
    def _write_raw(file: IO, chunk: bytes) -> None:
        """Write the `chunk` bytes to the file."""
        file.write(chunk)

    def _write_dict(self, file: IO, chunk: dict) -> None:
        """Write the `chunk` dictionary to the file."""
        file.write(bytes(f"{json.dumps(chunk)}\n", encoding=self.locale_encoding))
