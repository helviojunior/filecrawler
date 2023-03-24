#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import errno
import os, sys
import sqlite3
from os.path import expanduser
from pathlib import Path
import yaml
import re

from .libs.crawlerdb import CrawlerDB
from .parserbase import ParserBase
from .rulebase import RuleBase
from .util.color import Color
from .util.logger import Logger
from .__meta__ import __version__, __description__
from .util.tools import Tools
from yaml.loader import SafeLoader, FullLoader


class Configuration(object):
    ''' Stores configuration variables and functions for Tfilecrawler. '''
    version = '0.0.0'
    name = ""

    initialized = False # Flag indicating config has been initialized
    verbose = 0
    module = None
    cmd_line = ''
    lib_path = ''
    index_name = None
    config_file = ''
    db_file = ''
    db_name = ''
    path = ''
    company = []
    tasks = 5
    tasks_integrator = 2

    indexed_chars = 1000000
    excludes = [
        '*/~*', '*/.idea/*', '*/.svn/*', '*/.pyenv/*',
        '*/*.svg', '*/*.jpeg', '*/*.jpg', '*/*.png',  '*/*.gif', '*/*.ico',
        '*/*.css', '*/*.html', '*/*.htm',
        '*/*.ttf', '*/*.woff', '*/*.wof2',
        '*/*.pyc',
        '*/*.exe', '*/*.dll', '*/*.msi',
        '*/*.emf', '*/*.bdb', '*/*.vox', '*/*.bin', '*/*.dat', '*/*.pkl',
        '*/*.parquet', '*/*.parq', '*/*.rsc',
    ]
    json_support = False
    filename_as_id = False
    add_filesize = True
    remove_deleted = True
    add_as_inner_object = False
    store_source = False
    index_empty_files = False
    attributes_support = False
    raw_metadata = False
    xml_support = False
    lang_detect = False
    jar_support = True
    apk_support = True
    git_support = True
    extract_files = True
    continue_on_error = True
    ignore_above = '10M'
    max_size = -1
    ocr_language = 'eng'
    ocr_enabled = True
    ocr_pdf_strategy = 'ocr_and_text'
    follow_symlinks = True

    @staticmethod
    def initialize():
        '''
            Sets up default initial configuration values.
            Also sets config values based on command-line arguments.
        '''

        Configuration.version = str(__version__)
        Configuration.name = str(__name__)

        Configuration.lib_path = os.path.join(os.path.abspath(os.path.dirname(__file__)), 'libs')

        # Only initialize this class once
        if Configuration.initialized:
            return

        Configuration.initialized = True

        Configuration.verbose = 0 # Verbosity level.
        Configuration.print_stack_traces = True

        # Overwrite config values with arguments (if defined)
        Configuration.load_from_arguments()


    @staticmethod
    def load_from_arguments():
        ''' Sets configuration values based on Argument.args object '''
        from .args import Arguments

        config_check = 0

        args = Arguments()

        a1 = sys.argv
        a1[0] = 'filecrawler'
        for a in a1:
            Configuration.cmd_line += "%s " % a

        module = args.get_module()

        Configuration.verbose = args.args.v

        if args.args.config_file is None or args.args.config_file.strip() == '':
            Logger.pl('{!} {R}error: filename is invalid {O}%s{R} {W}\r\n' % (
                args.args.config_file))
            exit(1)

        if os.path.exists(args.args.config_file) and not os.path.isfile(args.args.config_file):
            Logger.pl('{!} {R}error: filename is invalid {O}%s{R} {W}\r\n' % (
                args.args.config_file))
            exit(1)

        Configuration.config_file = args.args.config_file

        if args.args.create_config:
            if os.path.isfile(Configuration.config_file):
                Logger.pl(
                    '{!} {R}Error: The configuration already exists.\n'
                )
                sys.exit(1)

            Configuration.create_config()
            return

        try:
            ParserBase.list_parsers(verbose=Configuration.verbose >= 2)
        except Exception as e:
            Color.pl('{!} {R}error: failed to load parsers: {O}%s{W}\r\n' % str(e))
            exit(1)

        try:
            RuleBase.list_rules(verbose=Configuration.verbose)
        except Exception as e:
            Color.pl('{!} {R}error: failed to load rules: {O}%s{W}\r\n' % str(e))
            exit(1)

        if module is None:
            Color.pl('{!} {R}error: missing a mandatory option, use -h help{W}\r\n')
            exit(1)

        java_ver = Tools.get_java_version()
        if java_ver is None:
            Color.pl('{!} {R}error: Java Runtime not found{W}\r\n')
            exit(1)

        try:
            Tools.get_mime(__file__)
        except ImportError:
            Color.pl('{!} {R}error: failed to find libmagic. Check your installation{W}\r\n')
            Color.pl('     {O}Linux: apt-get install libmagic-dev{W}')
            Color.pl('     {O}MacOS: brew install libmagic{W}')
            Color.pl('     {O}Windows: report bug{W}')
            exit(1)

        if args.args.tasks:
            Configuration.tasks = int(float(args.args.tasks) * 0.8)
            Configuration.tasks_integrator = args.args.tasks - Configuration.tasks

        if Configuration.tasks < 1:
            Configuration.tasks = 1

        if Configuration.tasks > 100:
            Configuration.tasks = 100

        if Configuration.tasks_integrator < 1:
            Configuration.tasks_integrator = 1

        if Configuration.tasks_integrator > 50:
            Configuration.tasks_integrator = 50

        Color.pl('{+} {W}Startup parameters')
        Logger.pl('     {C}command line:{O} %s{W}' % Configuration.cmd_line)
        Logger.pl('     {C}java version:{O} %s{W}' % java_ver)
        Logger.pl('     {C}worker tasks:{O} %s{W}' % Configuration.tasks)
        Logger.pl('     {C}integrator tasks:{O} %s{W}' % Configuration.tasks_integrator)

        if Configuration.verbose > 0:
            Logger.pl('     {C}verbosity level:{O} %s{W}' % Configuration.verbose)

        Configuration.tasks = 5

        Logger.pl('     {C}module:{O} %s{W}' % module.name)

        if args.args.index_name is not None and args.args.index_name.strip(' .,') != '':
            Configuration.index_name = Tools.clear_string(args.args.index_name).replace(',', '_').replace('.', '_')

        if not Configuration.index_name:
            Color.pl(
                '{!} {R}error: index name {O}%s{R} is not valid.{W}\r\n' % args.args.index_name)
            exit(1)

        if args.args.path is None or args.args.path.strip() == '' or not os.listdir(args.args.path):
            Color.pl(
                '{!} {R}error: path {O}%s{R} is not valid.{W}\r\n' % args.args.path)
            exit(1)

        Configuration.path = str(Path(args.args.path).resolve())

        if not module.load_from_arguments(args.args):
            Configuration.mandatory()

        Configuration.module = module

        if module.check_database:
            Configuration.module.open_db(args=args.args, check=True)

        try:

            if not os.path.isfile(Configuration.config_file):
                Logger.pl(
                    '{!} {W}The configuration file does not exists.'
                )
                Logger.p(
                    '{!} {W}Do you want create an default file and continue? (Y/n): {W}')
                c = input()
                if c.lower() == 'n':
                    exit(0)
                    Logger.pl(' ')

                Configuration.create_config()

            with open(Configuration.config_file, 'r') as f:
                data = dict(yaml.load(f, Loader=yaml.FullLoader))
                if data is not None and data.get('general', None) is not None:
                    general = data.get('general', {})
                    #Logger.pl(data)

                    Configuration.indexed_chars = int(general.get('indexed_chars', Configuration.indexed_chars))
                    Configuration.excludes = general.get('excludes', Configuration.excludes)
                    Configuration.json_support = general.get('json_support', Configuration.json_support)
                    Configuration.filename_as_id = general.get('filename_as_id', Configuration.filename_as_id)
                    Configuration.add_filesize = general.get('add_filesize', Configuration.add_filesize)
                    Configuration.remove_deleted = general.get('remove_deleted', Configuration.remove_deleted)
                    Configuration.add_as_inner_object = general.get('add_as_inner_object', Configuration.add_as_inner_object)
                    Configuration.store_source = general.get('store_source', Configuration.store_source)
                    Configuration.attributes_support = general.get('attributes_support', Configuration.attributes_support)
                    Configuration.raw_metadata = general.get('raw_metadata', Configuration.raw_metadata)
                    Configuration.xml_support = general.get('xml_support', Configuration.xml_support)
                    Configuration.lang_detect = general.get('lang_detect', Configuration.lang_detect)
                    Configuration.continue_on_error = general.get('continue_on_error', Configuration.continue_on_error)
                    Configuration.ignore_above = general.get('ignore_above', Configuration.ignore_above)
                    Configuration.ocr = general.get('ocr', {}).get('language', Configuration.ocr_language)
                    Configuration.ocr_language = general.get('ocr', {}).get('language', Configuration.ocr_language)
                    Configuration.ocr_enabled = Tools.to_boolean(general.get('ocr', {}).get('enabled', Configuration.ocr_enabled))
                    Configuration.ocr_pdf_strategy = general.get('ocr', {}).get('pdf_strategy', Configuration.ocr_pdf_strategy)
                    Configuration.follow_symlinks = general.get('follow_symlinks', Configuration.follow_symlinks)
                    Configuration.jar_support = general.get('jar_support', Configuration.jar_support)
                    Configuration.apk_support = general.get('apk_support', Configuration.apk_support)
                    Configuration.git_support = general.get('git_support', Configuration.git_support)
                    Configuration.extract_files = general.get('extract_files', Configuration.extract_files)
                    Configuration.index_empty_files = general.get('index_empty_files', Configuration.index_empty_files)

                    # Lowercase
                    Configuration.excludes = [
                        x.lower().strip() for x in Configuration.excludes
                    ]

                    # .git folder has an specific parser to diff contents
                    Configuration.excludes += ['*/.git/*']

                    Configuration.excludes += [
                        x[:-1] for x in Configuration.excludes
                        if x[-2:] == '/*'
                    ]

                if not module.load_config(data):
                    Configuration.mandatory()

        except IOError as x:
            if x.errno == errno.EACCES:
                Color.pl('{!} {R}error: could not open {G}%s {O}permission denied{R}{W}\r\n' % Configuration.config_file)
                sys.exit(1)
            elif x.errno == errno.EISDIR:
                Color.pl('{!} {R}error: could not open {G}%s {O}it is an directory{R}{W}\r\n' % Configuration.config_file)
                sys.exit(1)
            else:
                Color.pl('{!} {R}error: could not open {G}%s{W}\r\n' % Configuration.config_file)
                sys.exit(1)

        excluded = next((
            x for x in Configuration.excludes
            if Path(Configuration.path.lower()).match(x)
        ), None)

        if excluded is not None:
            Color.pl('{!} {R}error: the path {G}%s{R} is excluded by {G}%s{W}\r\n' % (Configuration.path, excluded))
            sys.exit(1)

        ia = Configuration.ignore_above.lower()
        x = re.search(r'([0-9]+)([a-z]{0,1})', ia)
        if x:
            size = int(x.group(1))
            unit = x.group(2)
            if unit == '':
                Configuration.max_size = size
            elif unit == 'k':
                Configuration.max_size = size * 1024
            elif unit == 'm':
                Configuration.max_size = size * 1024 * 1024
            elif unit == 'g':
                Configuration.max_size = size * 1024 * 1024 * 1024
            else:
                Color.pl('{!} {R}error: invalid ignore_above size {G}%s{W}\r\n' % Configuration.ignore_above)
                sys.exit(1)

        iname = Tools.sanitize_filename(Configuration.index_name)
        db_name = Path(expanduser(f'~/.filecrawler/{iname}/filecrawler.db'))
        if args.args.db_file.strip() != '':
            db_name = Path(args.args.db_file.strip())

        if not db_name.resolve().parent.exists():
            db_name.resolve().parent.mkdir(parents=True)

        Configuration.db_name = str(db_name.resolve())

        Logger.pl('     {C}database file:{O} %s{W}' % Configuration.db_name)

        try:
            with(CrawlerDB(auto_create=True, db_name=Configuration.db_name)) as db:
                pass
        except sqlite3.OperationalError as e:
            Logger.pl(
                '{!} {R}error: the database file exists but is not an SQLite or table structure was not created.{W}\r\n')
            exit(1)
        except Exception as e:
            raise e

        Logger.pl('     {C}index path:{O} %s{W}' % Configuration.path)

        if Configuration.git_support:
            git_ver = Tools.get_git_version()
            if git_ver is None:
                Configuration.git_support = False
                Color.pl((
                    '{!} {O}Warning:{W} failed to find git client. Git crawling is disabled. '
                    'Check your installation{W}'))
                Color.pl('     {GR}Linux: apt-get install git{W}')
                Color.pl('     {GR}MacOS: brew install git{W}')
                Color.pl('     {GR}Windows: install git from https://gitforwindows.org/{W}')
            else:
                Logger.pl('     {C}git version:{O} %s{W}' % git_ver)

        Logger.pl('  ')

    @staticmethod
    def create_config():
        from .crawlerbase import CrawlerBase
        sample_config = {
            'general': {
                'indexed_chars': Configuration.indexed_chars,
                'excludes': Configuration.excludes,
                'json_support': Configuration.json_support,
                'filename_as_id': Configuration.filename_as_id,
                'jar_support': Configuration.jar_support,
                'apk_support': Configuration.apk_support,
                'git_support': Configuration.git_support,
                'add_filesize': Configuration.add_filesize,
                'remove_deleted': Configuration.remove_deleted,
                'add_as_inner_object': Configuration.add_as_inner_object,
                'store_source': Configuration.store_source,
                'index_empty_files': Configuration.index_empty_files,
                'attributes_support': Configuration.attributes_support,
                'raw_metadata': Configuration.raw_metadata,
                'xml_support': Configuration.xml_support,
                'lang_detect': Configuration.lang_detect,
                'continue_on_error': Configuration.continue_on_error,
                'ignore_above': Configuration.ignore_above,
                'extract_files': Configuration.extract_files,
                'ocr': {
                    'language': Configuration.ocr_language,
                    'enabled': Configuration.ocr_enabled,
                    'pdf_strategy': Configuration.ocr_pdf_strategy,
                },
                'follow_symlinks': Configuration.follow_symlinks
            }
        }

        # List all modules
        modules = CrawlerBase.list_modules()
        for k, m in modules.items():
            try:
                s = m.create_instance().get_config_sample()
                if s is not None:
                    sample_config.update(s)
            except Exception as e:
                if Configuration.verbose >= 1:
                    Tools.print_error(e)


        with open(Configuration.config_file, 'w') as f:
            yaml.dump(sample_config, f, sort_keys=False, default_flow_style=False)

        Logger.pl('{+} {W}Config file created at {O}%s{W}\n' % Configuration.config_file)

    @staticmethod
    def get_banner():
            Configuration.version = str(__version__)

            return '''\

{G}File Crawler {D}v%s{W}{G} by Helvio Junior{W}
{W}{D}%s{W}
{C}{D}https://github.com/helviojunior/filecrawler{W}
    ''' % (Configuration.version, __description__)


    @staticmethod
    def dump():
        ''' (Colorful) string representation of the configuration '''
        from .util.color import Color

        max_len = 20
        for key in Configuration.__dict__.keys():
            max_len = max(max_len, len(key))

        result  = Color.s('{W}%s  Value{W}\n' % 'Configuration Key'.ljust(max_len))
        result += Color.s('{W}%s------------------{W}\n' % ('-' * max_len))

        for (key,val) in sorted(Configuration.__dict__.items()):
            if key.startswith('__') or type(val) == staticmethod or val is None:
                continue
            result += Color.s("{G}%s {W} {C}%s{W}\n" % (key.ljust(max_len),val))
        return result
