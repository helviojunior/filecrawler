import datetime
import hashlib
import os
from pathlib import Path
from typing import Optional

from filecrawler.util.tools import Tools
from typing import TypeVar

TCPath = TypeVar("TCPath", bound="CPath")


class CPath(object):
    _path = None
    _hash = None
    _path_real = None
    _path_virtual = None

    def __init__(self, base_path: [str, Path],  path: [str, Path], container_path: TCPath = None):
        self._path = Path(path)

        if not self._path.exists():
            raise FileNotFoundError(f'Path not found: {self._path}')

        base_path = str(Path(base_path).resolve())
        self._path_real = str(self._path.resolve())
        self._path_virtual = self._path_real.replace(base_path, '').strip('\\/ ')

        if container_path is not None:
            self._path_real = container_path.path_real + f'/{self._path_virtual}'
            self._path_virtual = container_path.path_virtual + f'/{self._path_virtual}'

        self._path_virtual = '/' + self._path_virtual.replace('\\\\', '/').replace('\\', '/').replace('//', '/').lstrip('\\/ ')

    @property
    def name(self):
        if self._path is None:
            return None

        return self._path.name

    @property
    def path(self) -> Path:
        return self._path

    @property
    def path_real(self) -> str:
        return self._path_real

    @property
    def path_virtual(self) -> str:
        return self._path_virtual

    def __str__(self):
        return str(self._path_real)

    # Parser
    def parse(self):
        pass
