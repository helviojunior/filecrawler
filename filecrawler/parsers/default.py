import json
from pathlib import Path

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger
from filecrawler.parserbase import ParserBase


class DefaultParser(ParserBase):

    def __init__(self):
        super().__init__('Default', 'Parser for PDF files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        data = {'content': self.get_readable_data(file)}

        return data

    def parse_from_bytes(self, file_data: bytes) -> dict:
        data = {'content': self.get_readable_data(file_data)}

        return data
