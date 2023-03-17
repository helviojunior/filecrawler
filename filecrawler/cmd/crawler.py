import json
import os
import sqlite3
import threading
import time
import sys
import hashlib
from argparse import _ArgumentGroup, Namespace
from pathlib import Path

import elastic_transport

from filecrawler.config import Configuration
from filecrawler.crawlerbase import CrawlerBase
from filecrawler.libs.containerfile import ContainerFile
from filecrawler.libs.file import File
from filecrawler.libs.worker import Worker
from filecrawler.parserbase import ParserBase
from filecrawler.parsers.default import DefaultParser
from filecrawler.util.color import Color
from filecrawler.libs.database import Database
from filecrawler.libs.crawlerdb import CrawlerDB
from filecrawler.util.logger import Logger
from elasticsearch import Elasticsearch, BadRequestError
from urllib.parse import urlparse
import requests
requests.packages.urllib3.disable_warnings()

class Crawler(CrawlerBase):
    db_name = ''
    force = False
    check_database = False
    index_id = -1
    index_name = 'file_crawler'
    nodes = []

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
                'nodes': [{'url': 'http://10.10.10.10:9200'}],
                'bulk_size': 200,
                'byte_size': '500K',
                'flush_interval': '2s'
            }
        }

    def load_from_arguments(self, args: Namespace) -> bool:
        return True

    def load_config(self, config: dict) -> bool:
        import validators
        from urllib.parse import urlparse
        if config is not None and config.get('elasticsearch', None) is not None:
            elasticsearch = config.get('elasticsearch', {})

            try:
                self.nodes = [
                    {
                        'scheme': url.scheme,
                        'host': f'{url.netloc}:'.split(':', 1)[0],
                        'port': int((url.netloc.split(':')[1:2] or (9200,))[0])
                    }
                    for url in [
                        urlparse(n['url']) for n in elasticsearch.get('nodes', [])
                        if n.get('url', None) is not None and validators.url(n['url'])
                    ]
                ]
            except Exception as e:
                Color.pl('{!} {R}error parsing elastic nodes: {O}%s{W}\r\n' % str(e))
                sys.exit(1)

        if self.nodes is None or len(self.nodes) == 0:
            Color.pl('{!} {R}error: invalid elasticsearch nodes. Check configuration file.{W}\r\n')
            sys.exit(1)

        return True

    def run(self):
        # Change log level
        import warnings
        from elasticsearch.exceptions import ElasticsearchWarning
        warnings.simplefilter('ignore', ElasticsearchWarning)

        db = CrawlerDB(auto_create=False,
                       db_name=Configuration.db_name)

        # Insert/get index name
        self.index_id = db.insert_or_get_index(Configuration.index_name)

        es = Elasticsearch(self.nodes)
        if not es.indices.exists(index=Configuration.index_name):
            request_body = {
                "settings": {
                    "number_of_replicas": 1
                },

                'mappings': {
                    'properties': {
                            'indexing_date': {'type': 'date'},
                            'created': {'type': 'date'},
                            'last_accessed': {'type': 'date'},
                            'last_modified': {'type': 'date'},
                            'fingerprint': {'type': 'text'},
                            'filename': {'type': 'text'},
                            'extension': {'type': 'text'},
                            'mime_type': {'type': 'text'},
                            'file_size': {'type': 'long'},
                            'path_virtual': {'type': 'text'},
                            'path_real': {'type': 'text'},
                            'content': {'type': 'text'},
                            'metadata': {'type': 'text'},
                            'parser': {'type': 'text'},
                            'object_content': {'type': 'flattened'},
                            'aws_credentials': {'type': 'flattened'},
                            'credentials': {'type': 'flattened'},
                        }
                }
            }

            es.indices.create(
                index=Configuration.index_name,
                body=request_body
            )


        #print(self.index_id)

        #Logger.pl('{+} {C}Database created {O}%s{W}' % self.db_name)

        with Worker(callback=self.file_callback, per_thread_callback=self.thread_start_callback,
                    threads=Configuration.tasks) as t:
            t.start()

            t1 = threading.Thread(target=self.status,
                                  kwargs=dict(sync=t, text="Processed"))
            t1.daemon = True
            t1.start()

            try:

                for f in self.list_files(base_path=Path(Configuration.path), path=Path(Configuration.path)):
                    while t.count > 1000:
                        time.sleep(0.3)

                    t.add_item(f)

                while t.executed < 1 and t.count > 0:
                    time.sleep(0.3)

                while t.running and t.count > 0:
                    time.sleep(0.300)

            except KeyboardInterrupt as e:
                raise e
            finally:
                t.close()

    @staticmethod
    def ignore(file: File) -> bool:
        if file is None:
            return True

        if file.size > Configuration.max_size:
            return False

        return False

    def thread_start_callback(self, index, **kwargs):
        return CrawlerDB(auto_create=False,
                         db_name=Configuration.db_name)

    def file_callback(self, entry, thread_callback_data, **kwargs):
        self.process_file(db=thread_callback_data, file=entry)

    def status(self, text, sync):
        try:
            while sync.running:
                print(f' {text}: {sync.executed}', file=sys.stderr, end='\r', flush=True)
                time.sleep(0.3)
        except KeyboardInterrupt as e:
            raise e
        except:
            pass
        finally:
            try:
                size = os.get_terminal_size(fd=os.STDOUT_FILENO)
            except:
                size = 50

            print((" " * size), end='\r', flush=True)
            print((" " * size), file=sys.stderr, end='\r', flush=True)

    def list_files(self, base_path: Path, path: Path, recursive: bool = True, container_path: File = None):
        here = str(path.resolve())
        files = [
            Path(os.path.join(here, name)).resolve()
            for name in os.listdir(here)
            if os.path.isfile(os.path.join(here, name))
        ]

        for f in files:
            yield File(base_path, f, container_path)

        if recursive:
            dirs = [
                Path(os.path.join(here, name)).resolve()
                for name in os.listdir(here)
                if os.path.isdir(os.path.join(here, name))
            ]
            for d in dirs:
                yield from self.list_files(
                    base_path=base_path,
                    path=d,
                    recursive=recursive,
                    container_path=container_path)

    def process_file(self, db: CrawlerDB, file: File):

        if ContainerFile.is_container(file):
            with(ContainerFile(file)) as container:
                out_path = container.extract()
                for f in self.list_files( base_path=out_path, path=out_path, recursive=True, container_path=file):
                    self.process_file(db=db, file=f)
        else:

            if Crawler.ignore(file):
                return

            row = db.insert_or_get_file(
                **file.db_dict,
                index_id=self.index_id,
            )

            if row is None and not Configuration.continue_on_error:
                raise Exception(f'Cannot insert file: {file.path_real}')

            if row is not None and row['inserted']:
                #print(file.path_virtual)
                #Process file content
                parser = ParserBase.get_parser_instance(file.extension)
                data = file.db_dict
                data.update(dict(parser=parser.name))

                tmp = parser.parse(file)
                if tmp is not None:
                    data.update(**tmp)

                    creds = parser.lookup_credentials(data.get('content', ''))
                    if creds is not None:
                        data.update(creds)

                    if data.get('content', None) is not None and Configuration.indexed_chars > 0:
                        data['content'] = data['content'][:Configuration.indexed_chars]

                self.send_to_elastic(
                    db=db,
                    **data
                )

    def send_to_elastic(self, db: CrawlerDB, **data):

        id = data['fingerprint']
        if Configuration.filename_as_id:
            id = data['path_virtual']

        try:
            with(Elasticsearch(self.nodes, timeout=30, max_retries=10, retry_on_timeout=True)) as es:
                res = es.index(index=Configuration.index_name, id=id, document=data)
                if res is None or res.get('_shards', {}).get('successful', 0) == 0:
                    db.delete('file_index', fingerprint=data['fingerprint'])

                    if not Configuration.continue_on_error:
                        raise Exception(f'Cannot insert elasticsearch data: {res}')

        except elastic_transport.ConnectionError:
            #Delete from DB and continue
            db.delete('file_index', fingerprint=data['fingerprint'])










