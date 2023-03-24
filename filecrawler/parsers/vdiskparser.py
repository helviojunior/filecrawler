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


class VDiskParser(ParserBase):
    extensions = ['vmdk', 'vhd', 'vhdx']
    mime_types = []

    def __init__(self):
        super().__init__('Virtual Disk Parser', 'Parser for Virtual Disk files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        data = {'content': ''}

        #TODO: Implementar

        return data

