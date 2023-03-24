import json
from pathlib import Path

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger
from filecrawler.parserbase import ParserBase


class PDFParser(ParserBase):
    extensions = ['pdf']

    def __init__(self):
        super().__init__('PDF Parser', 'Parser for PDF files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration

        data = self.ocr_file(file)

        return data
