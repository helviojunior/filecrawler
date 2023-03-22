import datetime
import hashlib
import os
import tempfile
from pathlib import Path
from typing import Optional
from filecrawler.libs.file import File
from filecrawler.libs.process import Process
from filecrawler.util.tools import Tools
import shutil


class ContainerFile(object):
    _file = None
    _temp_path = None
    _defs = [
        dict(name='zip', extensions=['zip'], mime=['application/zip']),
        dict(name='rar', extensions=['rar'], mime=['application/x-rar-compressed', 'application/vnd.rar']),
        dict(name='bz', extensions=['bz'], mime=['application/x-bzip']),
        dict(name='bz2', extensions=['bz2'], mime=['application/x-bzip2']),
        dict(name='gz', extensions=['gz'], mime=['application/gzip']),
        dict(name='7z', extensions=['7z'], mime=['application/x-7z-compressed']),
        #dict(name='tar', extensions=['tar'], mime=['application/x-tar']),
        dict(name='apk', extensions=['apk'], mime=[]),
        dict(name='jar', extensions=['jar'], mime=[])
    ]

    def __init__(self, file_path: File):
        self._file = file_path

        if not self._file.path.exists():
            raise FileNotFoundError(f'File not found: {self._file}')

        self._temp_path = tempfile.TemporaryDirectory(prefix='filecrawler_').name

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        if self._temp_path is None:
            return

        if not os.path.exists(str(self._temp_path)):
            return

        try:
            import shutil
            shutil.rmtree(self._temp_path, ignore_errors=True)
        except:
            pass

    def __str__(self):
        return str(self._file)

    @staticmethod
    def is_container(file: File) -> bool:
        return any([
            x for x in ContainerFile._defs
            if file.extension in x.get('extensions', []) or file.mime in x.get('mime', [])
        ])

    def create_folder(self):
        p = Path(self._temp_path)
        if not p.exists():
            p.mkdir(parents=True)

    def extract(self) -> Optional[Path]:
        from inspect import getmembers, isfunction

        #Try first by extension and after by mime type
        # Some specific extensions like APK and JAR has application/zip mime
        name = next((
            x['name'] for x in ContainerFile._defs
            if self._file.extension in x.get('extensions', [])
        ), next((
            x['name'] for x in ContainerFile._defs
            if self._file.mime in x.get('mime', [])
        ), ''))
        extractor_fnc = next((
            getattr(self, f[0]) for f in getmembers(self.__class__, isfunction)
            if f[0] == f'extract_{name}'
        ), None)

        if extractor_fnc is None:
            return None

        if extractor_fnc() and os.path.isdir(self._temp_path):
            return Path(self._temp_path)

        return None

    def extract_7z(self) -> bool:
        from filecrawler.config import Configuration
        if not Configuration.extract_files:
            return False

        try:
            from py7zr import SevenZipFile
            with SevenZipFile(str(self._file.path), 'r') as zObject:
                zObject.extractall(path=self._temp_path)

            return True
        except:
            return False

    def extract_zip(self) -> bool:
        from filecrawler.config import Configuration
        if not Configuration.extract_files:
            return False

        try:
            from zipfile import ZipFile
            with ZipFile(str(self._file.path), 'r') as zObject:
                zObject.extractall(self._temp_path)

            return True
        except:
            return False

    def extract_rar(self) -> bool:
        from filecrawler.config import Configuration
        if not Configuration.extract_files:
            return False

        try:
            from rarfile import RarFile
            with RarFile(str(self._file.path), 'r') as rObject:
                rObject.extractall(path=self._temp_path)

            return True
        except:
            return False

    def extract_tar(self) -> bool:
        from filecrawler.config import Configuration
        if not Configuration.extract_files:
            return False

        try:
            #TODO: Check TAR Lib lib
            import tarfile
            with tarfile.open(str(self._file.path), 'r') as tObject:
                tObject.extractall(self._temp_path)
            return True
        except:
            return False

    def extract_gz(self) -> bool:
        from filecrawler.config import Configuration
        if not Configuration.extract_files:
            return False

        name = self._file.path.name.lower()

        if '.tgz' in name or 'tar.gz' in name:
            return self.extract_tar()

        self.create_folder()

        try:
            import gzip
            nf = os.path.join(self._temp_path, self._file.path.name.replace(f'.{self._file.path.suffix}', ''))
            with gzip.open(str(self._file.path), 'rb') as entrada:
                with open(nf, 'wb') as saida:
                    shutil.copyfileobj(entrada, saida)

            #Check if output file is an Tar file
            if Tools.get_mime(nf) == 'application/x-tar':
                os.unlink(nf)
                return self.extract_tar()
        except:
            return False

        return True

    def extract_bz(self) -> bool:
        return self.extract_bz2()

    def extract_bz2(self) -> bool:
        from filecrawler.config import Configuration
        if not Configuration.extract_files:
            return False

        try:
            self.create_folder()
            import bz2
            nf = os.path.join(self._temp_path, self._file.path.name.replace(f'.{self._file.path.suffix}', ''))
            with bz2.open(str(self._file.path), mode='rb') as entrada:
                with open(nf, 'wb') as saida:
                    shutil.copyfileobj(entrada, saida)

            return True
        except:
            return False

    def extract_jar(self) -> bool:
        from filecrawler.config import Configuration
        if not Configuration.jar_support:
            return False

        return self._apktool()

    def extract_apk(self) -> bool:
        from filecrawler.config import Configuration
        if not Configuration.apk_support:
            return False

        return self._apktool()

    def _apktool(self) -> bool:
        from filecrawler.config import Configuration

        (retcode, _, _) = Process.call(
            f'java -jar apktool_2.7.0.jar -f d "{self._file.path}" -o "{self._temp_path}"',
            cwd=os.path.join(Configuration.lib_path, 'bin'))

        if retcode != 0:
            try:
                from zipfile import ZipFile
                with ZipFile(str(self._file.path), 'r') as zObject:
                    zObject.extractall(self._temp_path)

                return True
            except:
                return False
