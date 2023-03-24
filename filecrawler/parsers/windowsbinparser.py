import json
import os
import sys
from pathlib import Path

import yaml

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.libs.process import Process
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger
from filecrawler.parserbase import ParserBase


class WindowsBinParser(ParserBase):
    extensions = ['exe', 'dll', 'ocx']
    mime_types = ['application/vnd.microsoft.portable-executable']

    def __init__(self):
        super().__init__('Windows Bin Parser', 'Parser for Windows Bin files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        data = {'content': ''}

        #TODO: Implementar parser
        # Extensoes conhecidas: .exe, .dll, .pyd, .ocx

        return data
