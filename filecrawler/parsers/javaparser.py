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


class JavaParser(ParserBase):
    extensions = []
    mime_types = ['application/x-java-applet']

    def __init__(self):
        super().__init__('Java Classes Parser', 'Parser for Java Classes files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        data = {'content': self.get_readable_data(file)}

        (retcode, out, _) = Process.call(
            f'javap -p "{file.path}"',
            cwd=str(file.path.parent))

        if retcode == 0:
            data['content'] = out

        return data

