import json
from pathlib import Path

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger
from filecrawler.parserbase import ParserBase


class OfficeParser(ParserBase):
    extensions = ['doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'odt', 'xlsm', 'xltm', 'xlsb']
    mime_types = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                  ]


    def __init__(self):
        super().__init__('Document Parser', 'Parser for Document files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration

        data = self.ocr_file(file)

        return data

