import json
import os
import sys
from argparse import _ArgumentGroup, Namespace
from pathlib import Path

from filecrawler._exceptions import IntegrationError
from filecrawler.config import Configuration
from filecrawler.crawlerbase import CrawlerBase
from filecrawler.util.color import Color
from filecrawler.libs.crawlerdb import CrawlerDB
from elasticsearch import Elasticsearch
import requests
import elastic_transport

from filecrawler.util.tools import Tools

requests.packages.urllib3.disable_warnings()


class Local(CrawlerBase):
    nodes = []
    out_path = None

    def __init__(self):
        super().__init__('local', 'Save leaks locally')

    def add_flags(self, flags: _ArgumentGroup):
        pass

    def add_commands(self, cmds: _ArgumentGroup):
        cmds.add_argument('-o',
                          action='store',
                          metavar='[folder path]',
                          type=str,
                          dest=f'local_out_path',
                          default='',
                          help=Color.s('Folder path to save leaks'))
        pass

    def get_config_sample(self) -> dict:
        return {}

    def load_from_arguments(self, args: Namespace) -> bool:

        if args.local_out_path is None or args.local_out_path.strip() == '' or not os.path.isdir(args.local_out_path):
            Color.pl(
                '{!} {R}error: path {O}%s{R} is not valid.{W}\r\n' % args.local_out_path)
            exit(1)

        self.out_path = str(Path(args.local_out_path).resolve())

        return True

    def load_config(self, config: dict) -> bool:
        return True

    def pre_run(self, **data):
        pass

    def integrate(self, **data):
        # Save only leaked data
        if 'credentials' not in data.keys():
            return

        id = data['fingerprint']

        #Try to parse json object_content
        try:
            data['object_content'] = json.loads(data.get('object_content', '{}'))
        except:
            pass

        # Try to parse json content
        try:
            data['content'] = json.loads(data.get('content', '{}'))
        except:
            pass

        filename = Path(os.path.join(self.out_path, f'{id}.json'))
        with(open(filename, 'w')) as f:
            f.write(json.dumps(data, default=Tools.json_serial, indent=2))

