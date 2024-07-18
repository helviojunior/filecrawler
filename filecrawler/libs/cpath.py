import datetime
import hashlib
import os
from pathlib import Path
from typing import Optional

from filecrawler.libs.color import Color
from filecrawler.util.tools import Tools
from typing import TypeVar

TCPath = TypeVar("TCPath", bound="CPath")


class CPath(object):
    _path = None
    _hash = None
    _path_real = None
    _path_virtual = None

    def __init__(self, base_path: [str, Path],  path: [str, Path], container_path: TCPath = None):
        self._path = Path(str(path))

        base_path = str(Path(base_path).resolve())
        self._path_real = str(self._path.resolve())
        self._path_virtual = self._path_real.replace(base_path, '').strip('\\/ ')

        if container_path is not None:
            self._path_real = container_path.path_real + f'/{self._path_virtual}'
            self._path_virtual = container_path.path_virtual + f'/{self._path_virtual}'

        self._path_virtual = '/' + self._path_virtual.replace('\\\\', '/').replace('\\', '/').replace('//', '/').lstrip('\\/ ')

        if not self._path.exists():
            from filecrawler.config import Configuration
            Color.pl('\n{!} {R}Error:{O} Path not found{W}'
                     '\n            {W}Real path.....: {G}%s{W}'
                     '\n            {W}Virtual path..: {G}%s{W}' % (self._path, self._path_real))
            raise FileNotFoundError(f'Path not found')

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
