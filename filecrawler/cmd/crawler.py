import os
import sqlite3
import time
from argparse import _ArgumentGroup, Namespace

from filecrawler.config import Configuration
from filecrawler.crawlerbase import CrawlerBase
from filecrawler.util.color import Color
from filecrawler.libs.database import Database
from filecrawler.libs.crawlerdb import CrawlerDB
from filecrawler.util.logger import Logger
import yaml
from yaml.loader import SafeLoader


class Crawler(CrawlerBase):
    db_name = ''
    force = False
    check_database = False
    index_id = -1

    def __init__(self):
        super().__init__('crawler', 'Crawler folder and files')

    def add_flags(self, flags: _ArgumentGroup):
        pass

    def add_commands(self, cmds: _ArgumentGroup):
        cmds.add_argument('--elastic',
                          action='store_true',
                          default=False,
                          dest=f'elastic',
                          help=Color.s('Crawler to elastic search'))

    def get_config_sample(self) -> dict:
        return {
            'elasticsearch': {
                'nodes': [{'url': 'http://172.31.18.31:9200'}],
                'bulk_size': 200,
                'byte_size': '500K',
                'flush_interval': '2s',
                'index': 'file_indexer'
            }
        }

    def load_from_arguments(self, args: Namespace) -> bool:

        return True

    def load_config(self, config: dict) -> bool:
        if config is not None and config.get('elasticsearch', None) is not None:
            elasticsearch = config.get('elasticsearch', {})

            #TODO: Implement parse data

        return True

    def run(self):
        db = CrawlerDB(auto_create=False,
                       db_name=Configuration.db_name)

        # Insert/get index name
        self.index_id = db.insert_or_get_index(Configuration.index_name)

        print(self.index_id)

        Logger.pl('{+} {C}Database created {O}%s{W}' % self.db_name)

