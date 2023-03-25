#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from argparse import _ArgumentGroup, Namespace

from .crawlerbase import CrawlerBase
from .util.color import Color

import argparse, sys


class Arguments(object):
    ''' Holds arguments used by the filecrawler '''
    modules = {}
    verbose = False
    args = None

    def __init__(self):
        self.verbose = any(['-v' in word for word in sys.argv])
        self.args = self.get_arguments()

    def _verbose(self, msg):
        if self.verbose:
            Color.pl(msg)

    @classmethod
    def get_module(cls):
        if len(Arguments.modules) == 0:
            Arguments.modules = CrawlerBase.list_modules()

        selected_modules = [
            mod for mod in Arguments.modules
            if any([f'--{mod}' == word.lower() for word in sys.argv])
        ]

        if len(selected_modules) > 1:
            Color.pl('{!} {R}error: missing a mandatory option, use -h help{W}\r\n')
            exit(1)

        mod = None
        if len(selected_modules) == 1:
            mod = Arguments.modules[selected_modules[0]].create_instance()

        return mod

    def get_arguments(self) -> Namespace:
        ''' Returns parser.args() containing all program arguments '''

        parser = argparse.ArgumentParser(
            usage=argparse.SUPPRESS,
            prog="filecrawler",
            add_help=False,
            epilog='Use "filecrawler [module] --help" for more information about a command.',
            formatter_class=lambda prog: argparse.HelpFormatter(prog, max_help_position=80, width=130))

        mod = self.get_module()

        modules_group = parser.add_argument_group('Available Integration Modules')
        self._add_modules(modules_group, mod)

        if mod is not None:
            commands_group = parser.add_argument_group('Available Module Commands')
            mod.add_commands(commands_group)

            mod.add_groups(parser)

            flags = parser.add_argument_group('Module Flags')
            mod.add_flags(flags)

        flags = parser.add_argument_group('Global Flags')
        self._add_flags_args(flags)

        parser.usage = self.get_usage(module=mod)

        return parser.parse_args()

    def _add_flags_args(self, flags: _ArgumentGroup):
        flags.add_argument('--index-name',
                           action='store',
                           metavar='[index name]',
                           type=str,
                           dest=f'index_name',
                           default='',
                           help=Color.s('Crawler name'))

        flags.add_argument('--path',
                           action='store',
                           metavar='[folder path]',
                           type=str,
                           dest=f'path',
                           default='',
                           help=Color.s('Folder path to be indexed'))

        flags.add_argument('--config',
                           action='store',
                           metavar='[config file]',
                           type=str,
                           default='./config.yml',
                           dest=f'config_file',
                           help=Color.s('Configuration file. (default: {G}./fileindex.yml{W})'))

        flags.add_argument('--db',
                           action='store',
                           metavar='[sqlite file]',
                           type=str,
                           default='',
                           dest=f'db_file',
                           help=Color.s('Filename to save status of indexed files. (default: {G}~/.filecrawler/{index_name}/indexer.db{W})'))

        flags.add_argument('-T',
                           action='store',
                           dest='tasks',
                           default=5,
                           metavar='[tasks]',
                           type=int,
                           help=Color.s('number of connects in parallel (per host, default: {G}16{W})'))

        flags.add_argument('--create-config',
                           action='store_true',
                           default=False,
                           dest=f'create_config',
                           help=Color.s('Create config sample'))

        flags.add_argument('--clear-session',
                           action='store_true',
                           default=False,
                           dest=f'clear_session',
                           help=Color.s('Clear old file status and reindex all files'))

        flags.add_argument('-h', '--help',
                           action='help',
                           help=Color.s('show help message and exit'))

        flags.add_argument('-v',
                           action='count',
                           default=0,
                           help=Color.s(
                               'Specify verbosity level (default: {G}0{W}). Example: {G}-v{W}, {G}-vv{W}, {G}-vvv{W}'
                           ))

    def _add_modules(self, modules_group: _ArgumentGroup, module: CrawlerBase = None):
        for m in Arguments.modules:
            help = Color.s(f'{Arguments.modules[m].description}')
            if module is not None:
                help = argparse.SUPPRESS
            modules_group.add_argument(f'--{m}',
                                       action='store_true',
                                       help=help)

    def get_usage(self, module: CrawlerBase = None):
        if module is None:
            return f'''
    filecrawler module [flags]'''
        else:
            return f'''
    filecrawler --{module.name.lower()} command [flags]'''
