import json

from filecrawler.libs.database import Database
from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class SQLite3Parser(ParserBase):
    extensions = []
    mime_types = ['application/vnd.sqlite3']

    def __init__(self):
        super().__init__('SQLite3 Parser', 'Parser for SQLite3 files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        from filecrawler.util.tools import Tools
        content = {}

        try:
            with Database(db_name=file.path, auto_create=False) as db:
                tables = db.select_raw('SELECT m.tbl_name AS table_name FROM sqlite_master AS m', args={})
                for t in tables:
                    rows = db.select(t['table_name'], **{})
                    content.update({t['table_name']: rows})
        except Exception as e:
            if Configuration.verbose >= 3:
                Tools.print_error(e)

        data = {'content': json.dumps(content, default=Tools.json_serial, sort_keys=False, indent=2)}
        return data

