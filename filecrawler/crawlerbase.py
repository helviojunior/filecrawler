import base64
import json
import os
import sqlite3
import threading
import time
import sys
from pathlib import Path
import importlib
import pkgutil
import random
import string
from argparse import _ArgumentGroup, ArgumentParser, Namespace

from filecrawler._exceptions import IntegrationError
from filecrawler.libs.module import Module

from filecrawler.config import Configuration
from filecrawler.gitfinder import GitFinder
from filecrawler.libs.containerfile import ContainerFile
from filecrawler.libs.cpath import CPath
from filecrawler.libs.file import File
from filecrawler.libs.worker import Worker
from filecrawler.parserbase import ParserBase
from filecrawler.util.color import Color
from filecrawler.libs.crawlerdb import CrawlerDB
from filecrawler.util.logger import Logger
from filecrawler.util.tools import Tools


class CrawlerBase(object):
    _stdout = None
    _stderr = None

    help_show = True
    check_database = True
    name = ''
    description = ''
    verbose = 0

    db_name = ''
    force = False
    read = 0
    ignored = 0
    integrated = 0
    index_id = -1
    index_name = 'file_crawler'

    def __init__(self, name, description, help_show=True):
        self.name = name
        self.description = description
        self.help_show = help_show
        CrawlerBase.get_system_defaults()
        pass

    def integrate(self, **data):
        raise Exception('Method "integrate" is not yet implemented.')

    def pre_run(self, **data):
        raise Exception('Method "integrate" is not yet implemented.')

    @classmethod
    def write_status(cls, text):
        print(text, file=CrawlerBase._stderr, end='\r', flush=True)

    @classmethod
    def clear_line(cls):
        try:
            size = os.get_terminal_size(fd=os.STDOUT_FILENO)
        except:
            size = 80

        print((" " * size), end='\r', flush=True)
        print((" " * size), file=CrawlerBase._stderr, end='\r', flush=True)

    @staticmethod
    def get_system_defaults():
        if CrawlerBase._stdout is None:
            CrawlerBase._stdout = sys.stdout

        if CrawlerBase._stderr is None:
            CrawlerBase._stderr = sys.stderr

    @classmethod
    def get_base_module(cls) -> str:
        file = Path(__file__).stem

        parent_module = f'.{cls.__module__}.'.replace(f'.{file}.', '').strip(' .')

        return '.'.join((parent_module, 'cmd'))

    @classmethod
    def list_modules(cls, help_show=True, verbose=False) -> dict:
        try:

            base_module = CrawlerBase.get_base_module()

            modules = {}

            base_path = os.path.join(
                Path(__file__).resolve().parent, 'cmd'
            )

            for loader, modname, ispkg in pkgutil.walk_packages([base_path]):
                if not ispkg:
                    if verbose:
                        Color.pl('{?} Importing module: %s' % f'{base_module}.{modname}')
                    importlib.import_module(f'{base_module}.{modname}')

            if verbose:
                Logger.pl('')

            for iclass in CrawlerBase.__subclasses__():
                t = iclass()
                if t.name in modules:
                    raise Exception(f'Duplicated Module name: {iclass.__module__}.{iclass.__qualname__}')

                if t.help_show is True or help_show is True:
                    modules[t.name] = Module(
                        name=t.name.lower(),
                        description=t.description,
                        module=str(iclass.__module__),
                        qualname=str(iclass.__qualname__),
                        class_name=iclass
                    )

            return modules

        except Exception as e:
            raise Exception('Error listing command modules', e)

    def print_verbose(self, text: str, min_level: int = 1):
        if self.verbose <= min_level:
            return

        Logger.pl('{?} {W}{D}%s{W}' % text)

    def get_config_sample(self) -> list:
        return []

    def add_flags(self, flags: _ArgumentGroup):
        pass

    def add_commands(self, cmds: _ArgumentGroup):
        pass

    def add_groups(self, parser: ArgumentParser):
        pass

    def load_from_arguments(self, args: Namespace) -> bool:
        raise Exception('Method "load_from_arguments" is not yet implemented.')

    def load_config(self, config: dict) -> bool:
        raise Exception('Method "load_config" is not yet implemented.')

    def get_temp_directory(self) -> Path:
        path = os.path.join(
            os.getcwd(),
            ''.join(random.choice(string.ascii_lowercase + string.ascii_uppercase) for i in range(20))
        )
        p = Path(path)
        p.mkdir(parents=True, exist_ok=True)

        return p

    def get_files(self, path):
        for file in os.listdir(path):
            p1 = os.path.join(path, file)
            if os.path.isfile(p1):
                yield p1
            elif os.path.isdir(p1):
                yield from self.get_files(p1)

    def run(self):
        with(CrawlerDB(auto_create=False,db_name=Configuration.db_name)) as db:
            # Insert/get index name
            self.index_id = db.insert_or_get_index(Configuration.index_name)

        self.pre_run()

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

        return CrawlerBase.ignore2(file.size, str(file.path).lower(), [])

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
                    f' {text} read: {CrawlerBase.read}, ignored: {CrawlerBase.ignored}, integrated: {CrawlerBase.integrated}')
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
                            self.integrate(**data)
                            CrawlerBase.integrated += 1
                        except IntegrationError:
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

                    CrawlerBase.read += 1

                    if CrawlerBase.ignore2(len(f_data.get('content', '')), f_data['path_real'], ['*/.git/*', '*/.git/']):
                        CrawlerBase.ignored += 1
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
                            CrawlerBase.ignored += 1
                        else:
                            self.integrate(**f_data)
                            CrawlerBase.integrated += 1

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

            if CrawlerBase.ignore(file):
                CrawlerBase.ignored += 1
                return

            CrawlerBase.read += 1

            if db.select_count('file_index', index_id=self.index_id, fingerprint=file.fingerprint) > 0:
                CrawlerBase.ignored += 1
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
                        CrawlerBase.ignored += 1
                    else:
                        self.integrate(**data)
                        CrawlerBase.integrated += 1

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