import json
import os
import sys
from pathlib import Path

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.libs.process import Process
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger
from filecrawler.parserbase import ParserBase


class JsonParser(ParserBase):
    extensions = ['json']
    mime_types = ['application/json']

    def __init__(self):
        super().__init__('JSON Parser', 'Parser for JSON files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        data = {'content': self.get_readable_data(file)}

        if Configuration.json_support:
            try:
                data['content'] = json.dumps(json.loads(data['content']), sort_keys=False, indent=2)
            except:
                pass

        return data

    def parse_from_bytes(self, file_data: bytes) -> dict:
        from filecrawler.config import Configuration
        data = {'content': self.get_readable_data(file_data)}

        if Configuration.json_support:
            try:
                data['content'] = json.dumps(json.loads(file_data.decode("UTF-8")), sort_keys=False, indent=2)
            except:
                pass

        return data
