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


class PcapParser(ParserBase):
    extensions = ['pcap', 'pcapx']
    mime_types = ['application/vnd.tcpdump.pcap']

    def __init__(self):
        super().__init__('PCAP Parser', 'Parser for PCAP files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        data = {'content': ''}

        #TODO: Parse PCAP files

        return data
