#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import base64
import datetime
import io
import os
import platform
import string, random, sys, re
import subprocess
import unicodedata
from tabulate import _table_formats, tabulate
from filecrawler.util.color import Color


class Tools:

    def __init__(self):
        pass

    @staticmethod
    def random_generator(size=6, chars=string.ascii_uppercase + string.digits):
        return ''.join(random.choice(chars) for x in range(size))

    @staticmethod
    def clear_line():
        sys.stderr.write("\033[K")
        sys.stdout.write("\033[K")  # Clear to the end of line

        try:
            size = os.get_terminal_size(fd=os.STDOUT_FILENO)
        except:
            size = 50

        print((" " * size), end='\r', flush=True)
        print((" " * size), file=sys.stderr, end='\r', flush=True)

    @staticmethod     
    def permited_char(s):
        if s.isalpha():
            return True
        elif bool(re.match("^[A-Za-z0-9:]*$", s)):
            return True
        elif s == ".":
            return True
        elif s == ",":
            return True
        elif s == "-":
            return True
        elif s == "_":
            return True
        else:
            return False

    @staticmethod
    def mandatory():
        Color.pl('{!} {R}error: missing a mandatory option, use -h help{W}\r\n')
        Tools.exit_gracefully(1)

    @staticmethod
    def exit_gracefully(code=0):
        exit(code)

    @staticmethod
    def count_file_lines(filename: str):
        def _count_generator(reader):
            b = reader(1024 * 1024)
            while b:
                yield b
                b = reader(1024 * 1024)

        with open(filename, 'rb') as fp:
            c_generator = _count_generator(fp.raw.read)
            # count each \n
            count = sum(buffer.count(b'\n') for buffer in c_generator)
            return count + 1

    @staticmethod
    def clear_string(text):
        return ''.join(filter(Tools.permited_char, Tools.strip_accents(text))).strip().lower()

    @staticmethod
    def strip_accents(text):
        try:
            text = unicode(text, 'utf-8')
        except NameError:  # unicode is a default on python 3
            pass

        text = unicodedata.normalize('NFD', text) \
            .encode('ascii', 'ignore').decode("utf-8")

        return str(text).strip()

    @staticmethod
    def get_tabulated(data: list) -> str:

        if len(data) == 0:
            return ''

        headers = [(h if len(h) > 2 and h[0:2] != '__' else ' ') for h in data[0].keys()]
        data = [item.values() for item in data]

        return tabulate(data, headers, tablefmt='psql')

    @staticmethod
    def sizeof_fmt(num, suffix="B", start_unit=""):
        started = False
        for unit in ["", "K", "M", "G", "T", "P", "E", "Z"]:
            if started or start_unit.upper() == unit:
                started = True
                if abs(num) < 1024.0:
                    return f"{num:3.1f} {unit}{suffix}"
                num /= 1024.0
        return f"{num:.1f} Y{suffix}"

    @staticmethod
    def permited_char_filename(s):
        if s.isalpha():
            return True
        elif bool(re.match("^[A-Za-z0-9]*$", s)):
            return True
        elif s == "-":
            return True
        elif s == "_":
            return True
        elif s == ".":
            return True
        else:
            return False

    @staticmethod
    def sanitize_filename(name):
        if name is None:
          return ''
        name = Tools.strip_accents(name.strip())
        while ('  ' in name):
            name = name.replace('  ', ' ')
        name = name.replace(' ', '-')
        while ('--' in name):
            name = name.replace('--', '-')
        return ''.join(filter(Tools.permited_char_filename, name))

    @staticmethod
    def get_java_version():
        """Returns the string for the current version of Java installed."""
        proc = subprocess.Popen(['java', '-version'], stderr=subprocess.PIPE)
        ver = None

        if proc.wait() == 0:
            for line in proc.stderr.read().splitlines():
                # E.g. java version "12.0.2" 2019-07-16
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                line = line.strip()
                ver = next(
                    (
                        ver[1:-1]
                        for ver in line.split(' ')
                        if 'version' in line and ver.startswith('"') and ver.endswith('"')
                    ), None)
                if ver is not None:
                    break

        return ver

    @staticmethod
    def get_git_version():
        """Returns the string for the current version of Git installed."""
        proc = subprocess.Popen(['git', '--version'], stdout=subprocess.PIPE)
        ver = None

        p = re.compile(r"version ([0-9]{1,3}\.[0-9]{1,3}\.[0-9]{1,3})")

        if proc.wait() == 0:
            for line in proc.stdout.read().splitlines():
                # E.g. git version 2.37.3
                if isinstance(line, bytes):
                    line = line.decode("utf-8")
                line = line.strip().lower()
                m = p.search(line)
                if m is not None and m.group(1) is not None:
                    ver = m.group(1)
                if ver is not None:
                    break

        return ver

    @staticmethod
    def to_datetime(epoch: [int, float]) -> datetime.datetime:
        return datetime.datetime(1970, 1, 1, 0, 0, 0) + datetime.timedelta(seconds=epoch)

    @staticmethod
    def to_boolean(text: [str, bool]) -> bool:
        return bool(text)

    @staticmethod
    def get_mime(file_path: str) -> str:
        return Tools.get_mimes(open(file_path, "rb").read(2048))

    @staticmethod
    def get_mimes(data: [str, bytes]) -> str:
        import magic
        from filecrawler.config import Configuration

        if isinstance(data, str):
            data = data.encode('utf-8', 'ignore')

        if len(data) > 2048:
            data = data[:2048]

        p = platform.system().lower()
        if p == 'windows':
            f = magic.Magic(mime=True, magic_file=os.path.join(Configuration.lib_path, 'libmagic_windows', 'magic.mgc'))
        else:
            f = magic.Magic(mime=True)

        try:
            return f.from_buffer(data).lower()
        except Exception as e:
            Tools.print_error(e)
            return 'application/octet-stream'


    @staticmethod
    def json_serial(obj):
        """JSON serializer for objects not serializable by default json code"""

        if isinstance(obj, (datetime.datetime, datetime.date)):
            return obj.strftime("%Y-%m-%dT%H:%M:%S.000Z")

        if isinstance(obj, bytes):
            return base64.b64encode(obj).decode("UTF-8")

        raise TypeError("Type %s not serializable" % type(obj))

    @staticmethod
    def print_error(error: Exception):
        from filecrawler.config import Configuration
        Color.pl('\n{!} {R}Error:{O} %s{W}' % str(error))

        if Configuration.verbose > 0 or True:
            Color.pl('\n{!} {O}Full stack trace below')
            from traceback import format_exc
            Color.p('\n{!}    ')
            err = format_exc().strip()
            err = err.replace('\n', '\n{W}{!} {W}   ')
            err = err.replace('  File', '{W}{D}File')
            err = err.replace('  Exception: ', '{R}Exception: {O}')
            Color.pl(err)