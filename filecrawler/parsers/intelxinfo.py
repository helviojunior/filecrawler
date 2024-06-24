import datetime, re
import errno
import os.path
from pathlib import Path

from filecrawler.libs.color import Color
from filecrawler.util.tools import Tools


class IntelXInfo(object):
    _dt_fmt = "%Y-%m-%d %H:%M:%S"

    class FileInfo(object):
        def __init__(self, name: str, date: datetime.datetime, bucket: str, id: str):
            self.name = name
            self.date = date
            self.bucket = bucket
            self.id = str(id).lower()

        def __eq__(self, other):
            if isinstance(other, Path):
                p = Path(str(other).lower())
                e = p.suffix.lower().strip('. ')
                fn = p.name.replace(f".{e}", "")
                return fn == self.id
            else:
                return str(other) == str(self)

        def __repr__(self):
            return str(self)

        def __str__(self):
            return f"{self.date.strftime(IntelXInfo._dt_fmt)},{self.id},{self.name},{self.bucket}"

    def __init__(self, path: [str, Path]):
        from filecrawler.config import Configuration

        self.info_list = []
        idx_name = -1
        idx_date = -1
        idx_bucket = -1
        idx_media = -1
        idx_sysid = -1
        max_idx = 0

        #Name,Date,Bucket,Media,Content Type,Size,System ID

        if not os.path.isfile(os.path.join(str(path), "Info.csv")):
            if not os.path.isfile(os.path.join(str(path), "info.csv")):
                return
            else:
                i_file = os.path.join(str(path), "info.csv")
        else:
            i_file = os.path.join(str(path), "Info.csv")

        try:

            with open(i_file, 'r', encoding="ascii", errors="surrogateescape") as f:
                line = f.readline()
                while line:
                    if line.endswith('\n'):
                        line = line[:-1]
                    if line.endswith('\r'):
                        line = line[:-1]

                    line = ''.join(filter(Tools.permited_char, line)).strip()
                    # remove ','
                    if (m := re.search(",[0-9]{4}-[0-9]{2}-[0-9]{2} [0-9]{2}:[0-9]{2}:[0-9]{2},", line)) is not None:
                        p1 = line[0:m.start()].strip(', ')
                        pn = p1.replace(',', '_')
                        line = line.replace(p1, pn)

                    line_parts = line.split(',')
                    if len(line_parts) >= 3:
                        if idx_name == -1:
                            # First line
                            for i, p in enumerate([p1.lower() for p1 in line_parts]):
                                if p == "name":
                                    idx_name = i
                                elif p == "date":
                                    idx_date = i
                                elif p == "bucket":
                                    idx_bucket = i
                                elif p == "media":
                                    idx_media = i
                                elif p == "system id" or p == "systemid":
                                    idx_sysid = i

                            if any([
                                i for i in [idx_name, idx_date, idx_bucket, idx_media, idx_sysid]
                                if i == -1
                            ]):
                                return

                            max_idx = max([idx_name, idx_date, idx_bucket, idx_media, idx_sysid])

                        else:

                            if len(line_parts) >= max_idx:
                                self.info_list.append(
                                    IntelXInfo.FileInfo(
                                        line_parts[idx_name],
                                        datetime.datetime.strptime(line_parts[idx_date], self._dt_fmt),
                                        line_parts[idx_bucket],
                                        line_parts[idx_sysid]
                                    )
                                )

                    try:
                        line = f.readline()
                    except:
                        pass

        except IOError as x:
            print(x)
            if Configuration.verbose >= 3:
                if x.errno == errno.EACCES:
                    Color.pl('{!} {R}error: could not open %s {O}permission denied{R}{W}' % i_file)
                elif x.errno == errno.EISDIR:
                    Color.pl('{!} {R}error: could not open %s {O}it is an directory{R}{W}' % i_file)
                else:
                    Color.pl('{!} {R}error: could not open %s: %s{W}' % (i_file, str(x)))
            return

    def get_info(self, file):
        from filecrawler.libs.file import File

        if isinstance(file, str):
            fp = Path(file)
        elif isinstance(file, File):
            fp = file.path_real
        else:
            fp = file

        return next(iter([
            fi for fi in self.info_list
            if fi.__eq__(fp)
        ]), None)
