import datetime
import hashlib
import os
from pathlib import Path
from typing import Optional

from filecrawler.libs.cpath import CPath
from filecrawler.parsers.intelxinfo import IntelXInfo
from filecrawler.util.tools import Tools


class File(CPath):
    _hash = None
    _fingerprint = None
    _stats = None
    _metadata = []
    _content = None
    _mime_type = None
    _size = 0
    _credentials = []
    _info = None
    _overwrite_date = None

    def __init__(self,
                 base_path: [str, Path],
                 file_path: [str, Path],
                 container_path: CPath = None,
                 info: str = None):
        super().__init__(
            base_path=base_path,
            path=file_path,
            container_path=container_path
        )
        self._info = str(info) if info is not None else None

        if not self._path.is_file():
            raise FileNotFoundError(f'Path is not a file instance: {self._path}')

        if isinstance(info, IntelXInfo.FileInfo):
            self._overwrite_date = Tools.to_epoch(info.date)
            # Try to update file time from information received
            try:
                os.utime(str(file_path), (self._overwrite_date, self._overwrite_date))
            except:
                pass

        self._stats = self._path.stat()
        if self._overwrite_date is None:
            self._overwrite_date = self._stats.st_ctime

    @property
    def fingerprint(self):
        if self._path is None:
            return None

        if self._fingerprint is not None:
            return self._fingerprint

        sha1sum = hashlib.sha1()
        #sha1sum.update(f'{self.hash}_{self._path_virtual}'.encode("utf-8"))
        sha1sum.update(f'{self.hash}_{self._path.name.lower()}'.encode("utf-8"))
        self._fingerprint = sha1sum.hexdigest()

        return self._fingerprint

    @property
    def size(self) -> int:
        return self._stats.st_size

    @property
    def hash(self):
        if self._path is None:
            return None

        if self._hash is not None:
            return self._hash

        sha1sum = hashlib.sha1()
        with open(self._path, 'rb') as source:
            block = source.read(2 ** 16)
            while len(block) != 0:
                sha1sum.update(block)
                block = source.read(2 ** 16)
        self._hash = sha1sum.hexdigest()

        return self._hash

    @property
    def extension(self) -> Optional[str]:
        if self._path is None:
            return None
        
        return self._path.suffix.lower().strip('. ')

    @property
    def mime(self) -> Optional[str]:
        if self._path is None:
            return None

        if self._mime_type is not None:
            return self._mime_type

        self._mime_type = Tools.get_mime(str(self._path))
        return self._mime_type

    @property
    def db_dict(self) -> dict:
        return dict(
            fingerprint=self.fingerprint,
            filename=self._path.name,
            extension=self.extension,
            mime_type=self.mime,
            file_size=self._stats.st_size,
            created=Tools.to_datetime(self._overwrite_date),
            last_accessed=Tools.to_datetime(self._stats.st_atime),
            last_modified=Tools.to_datetime(self._stats.st_mtime),
            indexing_date=datetime.datetime.utcnow(),
            path_real=self._path_real,
            path_virtual=self._path_virtual,
            info=self._info if self._info is not None and isinstance(self._info, str) else "",
        )

    def __str__(self):
        return str(self._path_real)

    # Parser
    def parse(self):
        pass
