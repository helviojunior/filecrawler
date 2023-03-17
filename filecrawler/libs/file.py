import datetime
import hashlib
import os
from pathlib import Path
from typing import Optional

from filecrawler.util.tools import Tools
from typing import TypeVar

TFile = TypeVar("TFile", bound="File")


class File(object):
    _file = None
    _hash = None
    _fingerprint = None
    _path_real = None
    _path_virtual = None
    _stats = None
    _metadata = []
    _content = None
    _mime_type = None
    _size = 0
    _credentials = []

    def __init__(self, base_path: [str, Path],  file_path: [str, Path], container_path: TFile = None):
        self._file = Path(file_path)

        if not self._file.exists():
            raise FileNotFoundError(f'File not found: {self._file}')

        base_path = str(Path(base_path).resolve())
        self._path_real = str(self._file.resolve())
        self._path_virtual = self._path_real.replace(base_path, '').strip('\\/ ')

        if container_path is not None:
            self._path_real = container_path.path_real + f'/{self._path_virtual}'
            self._path_virtual = container_path.path_virtual + f'/{self._path_virtual}'

        self._path_virtual = '/' + self._path_virtual.replace('\\\\', '/').replace('\\', '/').replace('//', '/').lstrip('\\/ ')

        self._stats = self._file.stat()

    @property
    def path(self) -> Path:
        return self._file

    @property
    def fingerprint(self):
        if self._file is None:
            return None

        if self._fingerprint is not None:
            return self._fingerprint

        sha1sum = hashlib.sha1()
        sha1sum.update(f'{self.hash}_{self._path_virtual}'.encode("utf-8"))
        self._fingerprint = sha1sum.hexdigest()

        return self._fingerprint

    @property
    def path_real(self) -> str:
        return self._path_real

    @property
    def path_virtual(self) -> str:
        return self._path_virtual

    @property
    def size(self) -> int:
        return self._stats.st_size

    @property
    def hash(self):
        if self._file is None:
            return None

        if self._hash is not None:
            return self._hash

        sha1sum = hashlib.sha1()
        with open(self._file, 'rb') as source:
            block = source.read(2 ** 16)
            while len(block) != 0:
                sha1sum.update(block)
                block = source.read(2 ** 16)
        self._hash = sha1sum.hexdigest()

        return self._hash

    @property
    def extension(self) -> Optional[str]:
        if self._file is None:
            return None
        
        return self._file.suffix.lower().strip('. ')

    @property
    def mime(self) -> Optional[str]:
        if self._file is None:
            return None

        if self._mime_type is not None:
            return self._mime_type

        self._mime_type = Tools.get_mime(str(self._file))
        return self._mime_type

    @property
    def db_dict(self) -> dict:
        return dict(
            fingerprint=self.fingerprint,
            filename=self._file.name,
            extension=self.extension,
            mime_type=self.mime,
            file_size=self._stats.st_size,
            created=Tools.to_datetime(self._stats.st_ctime),
            last_accessed=Tools.to_datetime(self._stats.st_atime),
            last_modified=Tools.to_datetime(self._stats.st_mtime),
            indexing_date=datetime.datetime.utcnow(),
            path_real=self._path_real,
            path_virtual=self._path_virtual,
        )

    def __str__(self):
        return str(self._path_real)

    # Parser
    def parse(self):
        pass
