import json
from pathlib import Path

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger
from filecrawler.parserbase import ParserBase


class PDFParser(ParserBase):
    extensions = ['doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx']

    def __init__(self):
        super().__init__('Microsoft Office Parser', 'Parser for Microsoft Office files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        import tika
        from tika import parser
        tika.TikaClientOnly = True

        parsed = parser.from_file(str(file.path))

        data = {}

        if Configuration.raw_metadata:
            data['metadata'] = json.dumps(parsed["metadata"], sort_keys=True, indent=2)

        content = parsed["content"]
        content = content.strip('\r\n ')
        while '\n\n\n' in content:
            content = content.replace('\n\n\n', '\n\n')

        data["content"] = content

        return data


