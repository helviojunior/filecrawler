from filecrawler.libs.file import File
from filecrawler.libs.process import Process
from filecrawler.parserbase import ParserBase


class JavaParser(ParserBase):
    extensions = []
    mime_types = ['application/x-java-applet']

    def __init__(self):
        super().__init__('Java Classes Parser', 'Parser for Java Classes files')

    def parse(self, file: File) -> dict:
        data = {'content': self.get_readable_data(file)}

        (retcode, out, _) = Process.call(
            f'javap -p "{file.path}"',
            cwd=str(file.path.parent))

        if retcode == 0:
            data['content'] = out

        return data

