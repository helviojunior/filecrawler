import json
import os
import importlib
import pkgutil
import random
import sqlite3
import string
from pathlib import Path
from typing import Optional

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.rulebase import RuleBase
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger


class ParserBase(object):
    name = ''
    description = ''
    verbose = 0
    extensions = []
    mime_types = []

    #Static
    _parsers = {}

    def __init__(self, name, description):
        self.name = name
        self.description = description
        pass

    @classmethod
    def get_parser_instance(cls, file_extension: str, mime: str):
        from filecrawler.parsers.default import DefaultParser

        if file_extension is None and mime is None:
            return DefaultParser()

        if file_extension is None:
            file_extension = ''
        else:
            file_extension = file_extension.strip()

        if mime is None:
            mime = ''
        else:
            mime = mime.strip()

        cls.list_parsers()
        return next(
            (
                p.create_instance() for k, p in ParserBase._parsers.items()
                if mime != '' and p.is_valid(extension='', mime=mime, mime_only=True)
            )
            , next(
                (
                    p.create_instance() for k, p in ParserBase._parsers.items()
                    if file_extension != '' and p.is_valid(extension=file_extension)
                )
                , DefaultParser()
            )
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
                Logger.pl('')

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
                    extensions=t.extensions,
                    mime_types=t.mime_types
                )

            ParserBase._parsers = parsers
            return ParserBase._parsers

        except Exception as e:
            raise Exception('Error listing parsers', e)

    def parse(self, file: File) -> dict:
        raise Exception('Method "parse" is not yet implemented.')

    def parse_from_bytes(self, file_data: bytes) -> dict:
        import tempfile
        with tempfile.NamedTemporaryFile(mode="wb") as tmp_parser:
            tmp_parser.write(file_data)

            return self.parse(File(
                base_path=os.path.dirname(tmp_parser.name),
                file_path=tmp_parser.name
            ))

    @classmethod
    def lookup_credentials(cls, data: [str, bytes]) -> Optional[dict]:
        if isinstance(data, bytes):
            data = data.decode("utf-8", "ignore")

        detect = RuleBase.detect(data)
        if detect is None:
            return None

        detect.update(dict(
            has_credential='credentials' in detect.keys()
        ))

        return detect

    @classmethod
    def ocr_file(cls, file: File) -> dict:
        from filecrawler.config import Configuration

        if not Configuration.ocr_enabled:
            return dict(metadata='', content='')

        import tika
        from tika import parser
        tika.TikaClientOnly = True

        headers = {
            "X-Tika-OCRLanguage": f"eng+{Configuration.ocr_language}",
            "X-Tika-PDFocrStrategy": Configuration.ocr_pdf_strategy
        }
        parsed = parser.from_file(str(file.path), headers=headers)

        data = {}

        if Configuration.raw_metadata:
            not_meta = ['X-TIKA:', 'pdf:unmappedUnicodeCharsPerPage', 'pdf:charsPerPage',
                        'Content-Length', 'Content-Type', 'ICC:', 'tiff:']
            if data.get('metadata', None) is not None and isinstance(data.get('metadata', None), dict):
                data['metadata'] = json.dumps(
                    {
                        k: v for k, v in parsed["metadata"].items()
                        if not next((True for k1 in not_meta if k1.lower() in k.lower()), False)
                    },
                    sort_keys=True, indent=2)

        content = parsed["content"]
        if content is None:
            content = ''

        # Clear some items
        content = content.strip('\r\n ')
        content = content.replace('\t', '  ')
        while '\n\n\n' in content:
            content = content.replace('\n\n\n', '\n\n')

        data["content"] = content

        return data

    @classmethod
    def get_readable_data(cls, file: [File, bytes]) -> str:
        from filecrawler.config import Configuration

        if isinstance(file, File):
            with open(file.path, 'rb') as f:
                if Configuration.indexed_chars > 0:
                    bData = f.read(Configuration.indexed_chars)
                else:
                    bData = f.read()
        elif isinstance(file, bytes):
            bData = file
        else:
            bData = bytes()

        return bData.decode('utf-8', 'ignore')
