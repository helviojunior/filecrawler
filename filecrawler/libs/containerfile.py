import datetime
import hashlib
import os
import re
import tempfile
import pimht
from pathlib import Path
from urllib.parse import urlparse
from typing import Optional, Union

from filecrawler.util.tools import Tools

from filecrawler.libs.file import File
from filecrawler.libs.process import Process
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
        dict(name='eml', extensions=['eml'], mime=['message/rfc822']),
        dict(name='mht', extensions=['mht', 'mhtml'], mime=[]),
        #dict(name='tar', extensions=['tar'], mime=['application/x-tar']),
        dict(name='apk', extensions=['apk'], mime=[]),
        dict(name='jar', extensions=['jar', 'war'], mime=['application/java-archive'])
    ]
    _false_positive = [
        'doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'odt', 'xlsm', 'xltm', 'xlsb'
    ]

    def __init__(self, file_path: File):
        self._file = file_path

        if not self._file.path.exists():
            raise FileNotFoundError(f'File not found: {self._file}')

        self._temp_path = Tools.gettempdir(prefix='filecrawler_')

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
        if not isinstance(file, File):
            raise Exception("Invalid file type!")

        return any([
            x for x in ContainerFile._defs
            if (file.extension in x.get('extensions', []) or file.mime in x.get('mime', []))
            and file.extension.lower() not in ContainerFile._false_positive
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

    def extract_mht(self) -> bool:
        from filecrawler.config import Configuration
        if not Configuration.extract_files:
            return False

        self.create_folder()

        try:
            with open(str(self._file.path), "r") as f:
                f_data = f.read()

            try:
                if match := re.search(r"(;[ \r\n\t]{0,8})boundary=['\"][^'\"]+", f_data,
                                      flags=re.MULTILINE | re.IGNORECASE):
                    f_data = f_data.replace(match.group(0), match.group(0).replace(match.group(1), ';'))
            except:
                pass

            try:
                mhtml = pimht.from_string(f_data)

                for part in mhtml:
                    loc = part.headers.get('Content-Location', '')
                    output_filename = None
                    try:
                        url = urlparse(loc)
                        p = Path(url.path)
                        output_filename = str(p).lstrip("./\\")
                    except:
                        pass

                    if output_filename is None:
                        output_filename = Tools.random_generator(size=10) + Tools.guess_extensions(part.raw)

                    full_name = os.path.join(str(self._temp_path), output_filename)

                    try:
                        p1 = Path(full_name).parent
                        if str(p1) != str(self._temp_path):
                            os.makedirs(p1, exist_ok=True)
                    except:
                        pass

                    with open(full_name, "wb") as of:
                        try:
                            of.write(part.raw)
                        except TypeError:
                            print("Couldn't get payload for %s" % output_filename)

            except Exception as e:
                Tools.print_error(e)
                full_name = os.path.join(str(self._temp_path), 'body.txt')
                with open(full_name, "w") as of:
                    try:
                        of.write(f_data)
                    except:
                        pass

            return True
        except Exception as e:
            Tools.print_error(e)
            return False

    def extract_eml(self) -> bool:
        from filecrawler.config import Configuration
        if not Configuration.extract_files:
            return False

        self.create_folder()

        try:
            import glob
            import email
            from email import policy
            from email.parser import HeaderParser
            from filecrawler.util.tools import Tools

            with open(str(self._file.path), "r") as f:
                msg = email.message_from_file(f, policy=policy.default)
                msg_epoch = Tools.to_epoch(Tools.get_email_date(msg))
                msg_data = None

                full_name = os.path.join(str(self._temp_path), f"header.txt")
                try:
                    parser = HeaderParser()
                    with open(full_name, "wb") as of:
                        try:
                            of.write(f"## E-mail: {str(self._file.path)}\n".encode("UTF-8"))
                            of.write(f"## Header\n\n".encode("UTF-8"))
                            of.write(parser.parsestr(msg.as_string(), headersonly=True).as_string().encode("UTF-8"))
                        except:
                            pass
                except:
                    pass

                # Try to update file time from e-mail time
                try:
                    os.utime(full_name, (msg_epoch, msg_epoch))
                except:
                    pass

                if msg.is_multipart():
                    for t, ext in [('html', 'html'), ('plain', 'txt')]:
                        # Use txt instead of html, because html can be in exclusion list
                        full_name = os.path.join(str(self._temp_path), f"body_{ext}.txt")
                        try:
                            b_data = msg.get_body((t,))
                            if b_data is not None:
                                b_data = b_data.get_payload(decode=True)
                            if b_data is not None:
                                with open(full_name, "wb") as of:
                                    of.write(b_data)

                                # Try to update file time from e-mail time
                                try:
                                    os.utime(full_name, (msg_epoch, msg_epoch))
                                except:
                                    pass
                        except Exception as e1:
                            #Tools.print_error(e1)
                            pass

                    for attachment in msg.iter_attachments():
                        msg_data = None
                        try:
                            output_filename = attachment.get_filename()
                        except AttributeError:
                            print("Got string instead of filename for %s. Skipping." % f.name)
                            continue

                        msg_data = None
                        try:
                            msg_data = attachment.get_payload(decode=True)
                        except TypeError:
                            print("Couldn't get payload for %s" % output_filename)
                            continue

                        # If no attachments are found, skip this file
                        if msg_data is not None:
                            if output_filename is None:
                                output_filename = Tools.random_generator(size=10) + Tools.guess_extensions(msg_data)

                            full_name = os.path.join(str(self._temp_path), output_filename)

                            with open(full_name, "wb") as of:
                                try:
                                    of.write(msg_data)
                                except TypeError:
                                    print("Couldn't get payload for %s" % output_filename)

                            # Try to update file time from e-mail time
                            try:
                                os.utime(full_name, (msg_epoch, msg_epoch))
                            except:
                                pass

                # not multipart - i.e. plain text, no attachments, keeping fingers crossed
                else:
                    txt_body = msg.get_payload(decode=True)
                    full_name = os.path.join(str(self._temp_path), 'body.txt')
                    with open(full_name, "wb") as of:
                        try:
                            of.write(txt_body)
                        except:
                            pass

            return True
        except Exception as e:
            Tools.print_error(e)
            return False

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
        from filecrawler.util.tools import Tools
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

        #rc, _, _ = Process.call(
        #    f'java -jar apktool_2.7.0.jar -f d \'{self._file.path}\' -o \'{self._temp_path}\'',
        #    cwd=os.path.join(Configuration.lib_path, 'bin'))

        rc, _, _ = Process.call(
            f'/bin/bash jadx.sh -q -d \'{self._temp_path}\' \'{self._file.path}\'',
            cwd=os.path.join(Configuration.lib_path, 'bin'))

        if rc != 0:
            rc, _, _ = Process.call(
                f'java -jar apktool.jar -f d \'{self._file.path}\' -o \'{self._temp_path}\'',
                cwd=os.path.join(Configuration.lib_path, 'bin'))

        # in case of error, try to extract as a Zip file
        if rc != 0:
            try:
                from zipfile import ZipFile
                with ZipFile(str(self._file.path), 'r') as zObject:
                    zObject.extractall(self._temp_path)

                return True
            except:
                return False

        return os.path.isdir(self._temp_path)
