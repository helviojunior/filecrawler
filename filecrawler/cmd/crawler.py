import base64
import json
import os
import re
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
from filecrawler.gitfinder import GitFinder
from filecrawler.libs.containerfile import ContainerFile
from filecrawler.libs.cpath import CPath
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

from filecrawler.util.tools import Tools

requests.packages.urllib3.disable_warnings()


class Crawler(CrawlerBase):
    db_name = ''
    force = False
    check_database = False
    index_id = -1
    index_name = 'file_crawler'
    nodes = []
    read = 0
    ignored = 0
    integrated = 0

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
                'nodes': [{'url': 'http://127.0.0.1:9200'}],
                #'bulk_size': 200,
                #'byte_size': '500K',
                #'flush_interval': '2s'
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
                            'fingerprint': {'type': 'keyword'},
                            'filename': {'type': 'text'},
                            'extension': {'type': 'keyword'},
                            'mime_type': {'type': 'keyword'},
                            'file_size': {'type': 'long'},
                            'path_virtual': {'type': 'text'},
                            'path_real': {'type': 'text'},
                            'content': {'type': 'text'},
                            'metadata': {'type': 'text'},
                            'has_credential': {'type': 'boolean'},
                            'parser': {'type': 'keyword'},
                            'object_content': {'type': 'text'},
                            'credentials': {'type': 'flattened'},
                        }
                }
            }

            es.indices.create(
                index=Configuration.index_name,
                body=request_body
            )



        #Logger.pl(self.index_id)

        #Logger.pl('{+} {C}Database created {O}%s{W}' % self.db_name)

        with Worker(callback=self.file_callback, per_thread_callback=self.thread_start_callback,
                    threads=Configuration.tasks) as t:
            t.start()

            with Worker(callback=self.integrator_callback, per_thread_callback=self.thread_start_callback,
                        threads=Configuration.tasks_integrator) as ing:
                ing.start()

                t1 = threading.Thread(target=self.status,
                                      kwargs=dict(sync=t, text=""))
                t1.daemon = True
                t1.start()

                t2 = threading.Thread(target=self.integrator_selector,
                                      kwargs=dict(worker=ing))
                t2.daemon = True
                t2.start()

                try:

                    fl_count = 0
                    for f in self._list_objects(base_path=Path(Configuration.path), path=Path(Configuration.path)):
                        if not t.running or not ing.running:
                            break

                        while t.count > 1000:
                            time.sleep(0.3)

                        fl_count += 1
                        t.add_item(f)

                    Logger.pl('{+} {C}file list finished with {O}%s{C} files, waiting processors...{W}' % fl_count)

                    t.wait_finish()
                    ing.wait_finish()

                    Color.clear_entire_line()
                    Logger.pl('{+} {C}processors finished!{W}')

                except KeyboardInterrupt as e:
                    raise e
                finally:
                    t.close()
                    ing.close()

    @staticmethod
    def ignore(file: File) -> bool:
        if file is None:
            return True

        if file.size > Configuration.max_size:
            return True

        ignore = next((
            True for x in Configuration.excludes
            if Path(str(file.path).lower()).match(x)
        ), False)

        return Crawler.ignore2(file.size, str(file.path).lower(), [])

    @staticmethod
    def ignore2(size: int, path: str, include: list) -> bool:
        if size > Configuration.max_size:
            return True

        if path is None:
            return True

        ignore = next((
            True for x in [
                x1 for x1 in Configuration.excludes
                if x1 not in include
            ]
            if Path(str(path).lower()).match(x)
        ), False)

        return ignore

    def thread_start_callback(self, index, **kwargs):
        return CrawlerDB(auto_create=False,
                         db_name=Configuration.db_name)

    def file_callback(self, worker, entry, thread_callback_data, thread_count, **kwargs):
        try:
            if isinstance(entry, File):
                self.process_file(db=thread_callback_data, file=entry)
            elif isinstance(entry, CPath):
                self.process_path(db=thread_callback_data, path=entry)
        except KeyboardInterrupt as e:
            worker.close()
        except Exception as e:
            Tools.print_error(e)

    def status(self, text, sync):
        try:
            while sync.running:
                self.write_status(
                    f' {text} read: {Crawler.read}, ignored: {Crawler.ignored}, integrated: {Crawler.integrated}')
                time.sleep(0.3)
        except KeyboardInterrupt as e:
            raise e
        except:
            pass
        finally:
            self.clear_line()

    def integrator_callback(self, worker, entry, thread_callback_data, thread_count, **kwargs):
        try:
            #self.process_file(db=thread_callback_data, file=entry)
            file_id = int(entry)
            db = thread_callback_data
            try:
                dt = db.select_first('file_index', file_id=file_id, integrated=0, index_id=self.index_id)
                if dt is not None:
                    b64_data = dt.get('data', None)

                    if b64_data is None or b64_data.strip() == '':
                        Logger.pl(f'Data is empty to {file_id}')
                        Logger.p(dt)

                    if b64_data is not None and b64_data.strip() != '':
                        data = base64.b64decode(b64_data)
                        if isinstance(data, bytes):
                            data = data.decode("utf-8")

                        data = json.loads(data)

                        try:
                            self.send_to_elastic(**data)
                            Crawler.integrated += 1
                        except elastic_transport.ConnectionError:
                            time.sleep(0.3)
                            return
                        except Exception as e:
                            if not Configuration.continue_on_error:
                                Color.pl(
                                    '{!} {R}error: Cannot integrate file {G}%s{R}: {O}%s{W}\r\n' % (
                                    dt.get('path_virtual', ''), str(e)))
                                raise KeyboardInterrupt()

                    #Crawler.integrated += 1
                    db.update('file_index', filter_data=dict(file_id=file_id), integrated=1, data='')

            except sqlite3.OperationalError as e:
                if 'locked' in str(e):
                    time.sleep(5)

        except KeyboardInterrupt as e:
            worker.close()
        except Exception as e:
            Tools.print_error(e)

    def integrator_selector(self, worker):
        try:
            with(CrawlerDB(auto_create=False,
                           db_name=Configuration.db_name)) as db:
                while worker.running:

                    while worker.count > 500:
                        time.sleep(0.3)

                    try:
                        rows = db.select_raw(
                            sql='select file_id from [file_index] where integrated = 0 order by indexing_date limit 1000',
                            args=[]
                        )
                        if rows is not None and len(rows) > 0:
                            for r in rows:
                                worker.add_item(int(r['file_id']))
                    except sqlite3.OperationalError as e:
                        if 'locked' in str(e):
                            time.sleep(5)

                    time.sleep(5)

        except KeyboardInterrupt as e:
            worker.close()
        except Exception as e:
            Tools.print_error(e)

    def _list_objects(self, base_path: Path, path: Path, recursive: bool = True, container_path: File = None):
        here = str(path.resolve())
        files = [
            Path(os.path.join(here, name)).resolve()
            for name in os.listdir(here)
            if os.path.isfile(os.path.join(here, name))
        ]

        for f in files:
            yield File(base_path, f, container_path)

        if os.path.isdir(os.path.join(here, '.git')) and Configuration.git_support:
            yield CPath(base_path, Path(os.path.join(here, '.git')).resolve(), container_path)

        if recursive:
            dirs = [
                Path(os.path.join(here, name)).resolve()
                for name in os.listdir(here)
                if os.path.isdir(os.path.join(here, name)) and next((
                    False for x in Configuration.excludes
                    if Path(str(os.path.join(here, name)).lower()).match(x)
                    ), True)
            ]

            for d in dirs:
                yield from self._list_objects(
                    base_path=base_path,
                    path=d,
                    recursive=recursive,
                    container_path=container_path)

    def process_path(self, db: CrawlerDB, path: CPath):
        if path.name == '.git' and Configuration.git_support:
            try:
                git = GitFinder(path)
                for f_data in git.get_diffs():

                    Crawler.read += 1

                    if Crawler.ignore2(len(f_data.get('content', '')), f_data['path_real'], ['*/.git/*', '*/.git/']):
                        Crawler.ignored += 1
                        continue

                    parser = ParserBase.get_parser_instance(f_data['extension'], f_data['mime_type'])
                    f_data.update(dict(parser=parser.name))

                    tmp = parser.parse_from_bytes(f_data.get('content', bytes()))
                    if tmp is not None:
                        f_data.update(**tmp)

                        creds = parser.lookup_credentials(f_data.get('content', bytes()))
                        if creds is not None:
                            f_data.update(creds)
                            self.save_credential(f_data['path_virtual'], f_data.get('content', bytes()), creds)

                        if f_data.get('content', None) is not None and Configuration.indexed_chars > 0:
                            f_data['content'] = f_data['content'][:Configuration.indexed_chars]

                    b64_data = base64.b64encode(json.dumps(f_data, default=Tools.json_serial).encode("utf-8"))
                    if isinstance(b64_data, bytes):
                        b64_data = b64_data.decode("utf-8")

                    # try to send in a first attempt
                    integrated = 0
                    try:

                        if isinstance(f_data.get('content', ''), bytes):
                            f_data['content'] = f_data.get('content', bytes()).decode('utf-8', 'ignore')

                        if f_data.get('content', None) is not None and Configuration.indexed_chars > 0:
                            f_data['content'] = f_data['content'][:Configuration.indexed_chars]

                        f_data['content'] = f_data.get('content', '').strip('\n\t ')

                        if not Configuration.index_empty_files and \
                                (f_data.get('content', None) is None or len(f_data.get('content', '')) == 0):
                            Crawler.ignored += 1
                        else:
                            self.send_to_elastic(**f_data)
                            Crawler.integrated += 1

                        integrated = 1
                        b64_data = ''
                    except Exception as e:
                        if Configuration.verbose >= 4:
                            Tools.print_error(Exception(f'Error integrating git data from: {path.path_virtual}', str(e)))
                        pass

                    row = None
                    last_error = None
                    for i in range(50):
                        try:
                            row = db.insert_or_get_file(
                                **f_data,
                                index_id=self.index_id,
                                integrated=integrated,
                                data=b64_data
                            )
                            if row is None:
                                last_error = Exception('database register is none')
                            break
                        except sqlite3.OperationalError as e:
                            last_error = e
                            if 'locked' in str(e):
                                time.sleep(0.5 * float(i))
                                if i >= 20:
                                    db.reconnect()
                    if row is None and not Configuration.continue_on_error:
                        Color.pl(
                            '{!} {R}error: Cannot insert file {G}%s{R}: {O}%s{W}\r\n' % (path.path_real, str(last_error)))
                        raise KeyboardInterrupt()
            except KeyboardInterrupt as e:
                raise e
            except Exception as e:
                if Configuration.verbose >= 3:
                    Tools.print_error(Exception(f'Error getting git data from: {path.path_virtual}', e))

    def process_file(self, db: CrawlerDB, file: File):

        if Configuration.verbose >= 3:
            Color.pl('{*} {GR}processing %s{W}' % file.path_virtual)

        if ContainerFile.is_container(file):
            with(ContainerFile(file)) as container:
                out_path = container.extract()
                if out_path is not None:
                    for f in self._list_objects(base_path=out_path, path=out_path, recursive=True, container_path=file):
                        if isinstance(f, File):
                            self.process_file(db=db, file=f)
                        elif isinstance(f, CPath):
                            self.process_path(db=db, path=f)

        else:

            if Crawler.ignore(file):
                Crawler.ignored += 1
                return

            Crawler.read += 1

            if db.select_count('file_index', index_id=self.index_id, fingerprint=file.fingerprint) > 0:
                Crawler.ignored += 1
                return

            row = None
            last_error = None
            for i in range(50):
                try:
                    row = db.insert_or_get_file(
                        **file.db_dict,
                        index_id=self.index_id,
                        integrated=1, # To not try to integrate without content
                    )
                    if row is None:
                        last_error = Exception('database register is none')
                    break
                except sqlite3.OperationalError as e:
                    last_error = e
                    if 'locked' in str(e):
                        time.sleep(0.5 * float(i))
                        if i >= 20:
                            db.reconnect()

            if row is None and not Configuration.continue_on_error:
                Color.pl(
                    '{!} {R}error: Cannot insert file {G}%s{R}: {O}%s{W}\r\n' % (file.path_real, str(last_error)))
                raise KeyboardInterrupt()

            if row is not None and row['inserted']:
                #Logger.pl(file.path_virtual)
                #Process file content
                parser = ParserBase.get_parser_instance(file.extension, file.mime)
                data = file.db_dict
                data.update(dict(parser=parser.name))

                tmp = parser.parse(file)
                if tmp is not None:
                    data.update(**tmp)

                    creds = parser.lookup_credentials(data.get('content', ''))
                    if creds is not None:
                        data.update(creds)
                        self.save_credential(file.path_virtual, data.get('content', ''), creds)

                    if data.get('content', None) is not None and Configuration.indexed_chars > 0:
                        data['content'] = data['content'][:Configuration.indexed_chars]

                b64_data = base64.b64encode(json.dumps(data, default=Tools.json_serial).encode("utf-8"))
                if isinstance(b64_data, bytes):
                    b64_data = b64_data.decode("utf-8")

                # try to send in a first attempt
                integrated = 0
                try:

                    if isinstance(data.get('content', ''), bytes):
                        data['content'] = data.get('content', bytes()).decode('utf-8', 'ignore')

                    if data.get('content', None) is not None and Configuration.indexed_chars > 0:
                        data['content'] = data['content'][:Configuration.indexed_chars]

                    data['content'] = data.get('content', '').strip('\n\t ')

                    if not Configuration.index_empty_files and \
                            (data.get('content', None) is None or len(data.get('content', '')) == 0):
                        Crawler.ignored += 1
                    else:
                        self.send_to_elastic(**data)
                        Crawler.integrated += 1

                    integrated = 1
                    b64_data = ''
                except:
                    pass

                for i in range(5):
                    try:
                        db.update('file_index',
                                  filter_data=dict(file_id=row['file_id']),
                                  **dict(
                                      integrated=integrated,
                                      data=b64_data
                                  )
                        )
                        break
                    except sqlite3.OperationalError as e:
                        if 'locked' in str(e):
                            time.sleep(1)

        if Configuration.verbose >= 3:
            Color.pl('{*} {GR}finishing processor for %s{W}' % file.path_virtual)

    def save_credential(self, file_path: str, content: str, credentials: dict):
        if credentials is None:
            return

        if Configuration.verbose >= 2:
            Color.pl('{?} {GR}Credential found at file {O}%s{GR}\n%s{W}\n' % (
                file_path, json.dumps(credentials, default=Tools.json_serial, indent=2)))
        elif Configuration.verbose >= 1:
            Color.pl('{?} {GR}Credential found at file {O}%s{GR}' % file_path)

    def send_to_elastic(self, **data):
        id = data['fingerprint']
        if Configuration.filename_as_id:
            id = data['path_virtual']

        with(Elasticsearch(self.nodes, timeout=30, max_retries=10, retry_on_timeout=True)) as es:
            res = es.index(index=Configuration.index_name, id=id, document=data)
            if res is None or res.get('_shards', {}).get('successful', 0) == 0:
                if not Configuration.continue_on_error:
                    raise Exception(f'Cannot insert elasticsearch data: {res}')

            return res

            #if res.get('result', '') != 'created':
            #    Logger.pl(res)











