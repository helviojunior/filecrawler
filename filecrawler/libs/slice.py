import re
from pathlib import Path
from ansi2image.ansi2image import Ansi2Image

from filecrawler.config import Configuration
from filecrawler.libs.color import Color
from filecrawler.util.tools import Tools


class Slice(object):
    _filename = None
    _line_filter = []
    _table = ''

    def __init__(self, file_path: str, fingerprint: str, content: str, credentials: dict):

        self._filename = Path(file_path)

        if credentials is None or len(credentials) == 0:
            return

        findings = self._get_findings(credentials.get('credentials', {}))
        if len(findings) == 0:
            return

        #content = Slice.escape_ansi(content.replace('\r', ''))
        content = content.replace('\r', '')
        for f in findings:
            content = content.replace(f, '{R}%s{GR}' % f)

        content = Color.s(content)

        lines = content.split('\n')
        highlight_filter = [
            i
            for i, line in enumerate(lines)
            if any(
                True for f in findings
                if f in line
            )
        ]
        if len(highlight_filter) == 0:
            return

        self._line_filter = []

        # Add edge lines (5 before and 5 after)
        for i in highlight_filter:
            bs = i - 5
            if bs < 0:
                bs = 0

            ae = i + 5
            if ae > len(lines):
                ae = len(lines)

            self._line_filter += [(bs, ae)]

        mc = len(f'{len(lines)}')
        dot_line = Color.s('  {W}%s{W}  ' % Slice.format_line_number('...', mc))
        c1_len = len(Slice.escape_ansi(dot_line))
        data = [
            (
                Color.s(' {W}{O}{D}%s{GR}:{W}  ' % Slice.format_line_number(i + 1, mc)) +
                Slice.format_line(l, c1_len)
            )
            if self.is_valid(i + 1) else dot_line
            for i, l in enumerate(lines)
            if self.is_valid(i + 1) or self.is_dot(i + 1)
        ]

        if not self.is_valid(len(lines)):
            data += [dot_line]

        self._table = ' \033[38;5;52m=\033[38;5;88m=\033[38;5;124m=\033[38;5;160m=\033[38;5;196m> ' + Color.s(
            '{W}{O}Id   {G}%s{W}\n' % fingerprint)
        p1 = ' \033[38;5;52m=\033[38;5;88m=\033[38;5;124m=\033[38;5;160m=\033[38;5;196m> ' + Color.s(
            '{W}{O}File ')
        p2 = Slice.format_line('{G}%s{W}' % file_path, len(Slice.escape_ansi(p1)))
        self._table += Color.s('%s%s\n' % (p1, p2))

        self._table += ''.join([
            '%s--' % c for k, c in sorted(Color.gray_scale.items(), key=lambda x:x[0], reverse=True)
        ]) + Color.s('{W}\n')

        self._table += '\n'.join(data)
        self._table += Color.s('\n{W}')

    @classmethod
    def _get_findings(cls, credentials) -> list:
        lst = []
        if isinstance(credentials, list):
            lst += [
                l0
                for l0 in credentials
                for _, d0 in l0.items()
                for l0 in d0.get('findings', [])
                if isinstance(d0, dict) and d0.get('findings', None) is not None \
                   and isinstance(d0['findings'], list)
            ]
        elif isinstance(credentials, dict):
            lst += [
                l0
                for _, d0 in credentials.items()
                for l0 in d0.get('findings', [])
                if isinstance(d0, dict) and d0.get('findings', None) is not None \
                   and isinstance(d0['findings'], list)
            ]

        return [
            s for _, s in
            sorted({
                '%s_%s_%s' % (1 if k == 'match' else 0, i, k): v
                for i, l0 in enumerate(lst)
                for k, v in l0.items()
                if isinstance(l0, dict) and k not in ('fingerprint', 'severity', 'entropy') and isinstance(v, str)
            }.items(), key=lambda x:x[0], reverse=False)
            if s.strip() != ''
        ]

    @property
    def text(self):
        return self.escape_ansi(self._table)

    @property
    def ansi(self):
        return self._table

    @staticmethod
    def format_line(text: str, number_line: int) -> str:
        tab = 2
        text = text.replace('\t', ' ' * tab).rstrip() + ' '
        max_cols = 200
        if len(text) < max_cols:
            #print(text)
            return Color.s('{GR}%s{W}' % text)

        try:
            parts = []
            escaped_text = Slice.escape_ansi(text)
            diff = (len(escaped_text) - len(escaped_text.lstrip()))
            start = text.index(escaped_text.lstrip()[0]) - diff

            if start > 0:
                parts.append(text[0:start])

            pattern = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
            ansi_codes = [
                (m.start(), m.end())
                for m in pattern.finditer(text)
            ]

            c = max_cols
            o = start
            size = max_cols
            first_line = True
            while c <= len(text):
                p = text[o:c]
                while len(Slice.escape_ansi(p)) < size:
                    c += 1
                    p = text[o:c]
                    if o + c >= len(text):
                        break
                (idxs, idxe) = next((
                    a for a in ansi_codes
                    if a[0] <= c <= a[1]
                ), (None, None))
                if idxs is not None:
                    c = idxe
                p = text[o:c]
                if first_line:
                    size = max_cols - diff - tab
                    first_line = False
                else:
                    parts.append(' \n' + (' ' * (number_line + diff + tab)))
                o = c
                c += size
                parts.append(p)

            if o < len(text):
                parts.append(' \n' + (' ' * (number_line + diff + tab)))
                parts.append(text[o:])

            return Color.s('{GR}%s{W}' % ''.join(parts))
        except Exception as e:
            if Configuration.verbose >= 4:
                Tools.print_error(e)
            return text

    def is_valid(self, line):
        if len(self._line_filter) == 0:
            return True

        return any([
            x for x in self._line_filter
            if line >= x[0] and (x[1] == 0 or line <= x[1])
        ])

    def is_dot(self, line):
        if len(self._line_filter) == 0:
            return False

        if self.is_valid(line):
            return False

        return any([
            x for x in self._line_filter
            if x[0] != 0 and line == x[0] - 1
        ])

    @staticmethod
    def format_line_number(line, max_line):
        max_line = max_line if max_line > 3 else 3

        if line is None or str(line).strip() == '':
            return f''.rjust(max_line)
        elif str(line) == '...':
            return '{GR}%s' % (f'{line}'.rjust(max_line))
        elif isinstance(line, int):
            return '{O}{D}%s' % (f'{line}'.rjust(max_line))
        else:
            s = Slice.escape_ansi(line)
            return f''.rjust(max_line)[1:len(s)] + f'{line}'

    @staticmethod
    def escape_ansi(text):
        if text is None:
            return ''

        pattern = re.compile(r'(\x9B|\x1B\[)[0-?]*[ -/]*[@-~]')
        return pattern.sub('', text)

    def save_png(self, filename):
        o = Ansi2Image(0, 0, font_name=Ansi2Image.get_default_font_name(), font_size=13)
        if len(self._table.split('\n')) > 200:
            text = '\n'.join(self._table.split('\n')[0:200])
            text += Color.s('  {W}%s{W}  \n' % Slice.format_line_number('...', 3))
            text += Color.s('\n  {R}ATTENTION!!!{O} \n  %s{W}\n' % 'Displayed content is truncated due to maximum viewable content limit')
            o.loads(text)
        else:
            o.loads(self._table)
        o.min_margin = 10
        o.max_margin = 30
        o.calc_size(margin=0.01)
        o.save_image(filename, format='PNG')

    def save_evidences(self, base_path: [str, Path], fingerprint: str):
        if fingerprint is None or fingerprint.strip() == '':
            return

        base_name = Path(f'{base_path}/{fingerprint}').resolve()
        with open(f'{base_name}.ansi.txt', 'wb') as f:
            f.write(self.ansi.encode('utf-8', 'ignore'))

        self.save_png(f'{base_name}.png')
