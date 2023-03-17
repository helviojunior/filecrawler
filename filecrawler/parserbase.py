import os
import importlib
import pkgutil
import random
import sqlite3
import string
from pathlib import Path

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger


class ParserBase(object):
    name = ''
    description = ''
    verbose = 0
    extensions = []

    #Static
    _parsers = {}

    def __init__(self, name, description):
        self.name = name
        self.description = description
        pass

    @classmethod
    def get_parser_instance(cls, file_extension: str):
        from filecrawler.parsers.default import DefaultParser

        if file_extension is None:
            return DefaultParser()

        file_extension = file_extension.strip('. ')
        if file_extension == '':
            return DefaultParser()

        cls.list_parsers()
        return next(
            (
                p.create_instance() for k, p in ParserBase._parsers.items()
                if p.is_valid(file_extension)
            )
            , DefaultParser()
        )

    @classmethod
    def get_base_parsers(cls) -> str:
        file = Path(__file__).stem

        parent_module = f'.{cls.__module__}.'.replace(f'.{file}.', '').strip(' .')

        return '.'.join((parent_module, 'parsers'))

    @classmethod
    def list_parsers(cls, verbose=False) -> dict:
        try:

            if ParserBase._parsers is not None and len(ParserBase._parsers) > 0:
                return ParserBase._parsers

            base_parser = ParserBase.get_base_parsers()

            parsers = {}

            base_path = os.path.join(
                Path(__file__).resolve().parent, 'parsers'
            )

            for loader, modname, ispkg in pkgutil.walk_packages([base_path]):
                if not ispkg:
                    if verbose:
                        Color.pl('{?} Importing parser: %s' % f'{base_parser}.{modname}')
                    importlib.import_module(f'{base_parser}.{modname}')

            if verbose:
                print('')

            for iclass in ParserBase.__subclasses__():
                t = iclass()
                if t.name in parsers:
                    raise Exception(f'Duplicated Parser name: {iclass.__module__}.{iclass.__qualname__}')

                parsers[t.name] = Parser(
                    name=t.name.lower(),
                    description=t.description,
                    parser=str(iclass.__module__),
                    qualname=str(iclass.__qualname__),
                    class_name=iclass,
                    extensions=t.extensions
                )

            ParserBase._parsers = parsers
            return ParserBase._parsers

        except Exception as e:
            raise Exception('Error listing parsers', e)

    def parse(self, file: File) -> dict:
        raise Exception('Method "parse" is not yet implemented.')
