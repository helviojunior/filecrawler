import json
from pathlib import Path

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger
from filecrawler.parserbase import ParserBase


class ImageParser(ParserBase):
    extensions = ['png', 'jpg', 'jpeg', 'gif', 'emf']

    def __init__(self):
        super().__init__('Image Parser', 'Parser for Image files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration

        data = self.ocr_file(file)

        return data


