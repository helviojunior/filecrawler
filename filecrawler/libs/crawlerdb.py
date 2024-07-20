#!/usr/bin/python3
# -*- coding: UTF-8 -*-
from typing import Optional

from .database import Database


class CrawlerDB(Database):
    dbName = ""

    _FILE_INDEX_COLUMNS = ['file_id', 'index_id', 'fingerprint', 'filename', 'file_size', 'extension', 'mime_type',
                           'created', 'last_accessed', 'last_modified', 'indexing_date', 'path_real', 'path_virtual',
                           'data', 'integrated']

    _ALERT_COLUMNS = ['alert_id', 'index_id', 'file_fingerprint', 'fingerprint', 'data', 'sent']

    def __init__(self, auto_create=True, db_name=None):

        if db_name is None:
            db_name = "filecrawler.db"

        super().__init__(
            auto_create=auto_create,
            db_name=db_name
        )

    def has_data(self) -> bool:
        return self.select_count('file_index') > 0

    def check_open(self) -> bool:
        return self.select_count('file_index') >= 0

    def insert_or_get_index(self, index_name: str) -> int:

        if index_name is None or index_name.strip() == '':
            raise Exception('Domain cannot be empty')

        f = {
            'name': index_name.lower()
        }

        self.insert_update_one_exclude('index', **f)

        return self.select_first('index', **f).get('index_id', -1)

    def insert_or_get_file(self, **data) -> Optional[dict]:
        from filecrawler.config import Configuration

        if Configuration.disable_db:
            return {**data, **dict(inserted=1, updated=0)}

        for k in [k1 for k1 in data.keys()]:
            if k not in self._FILE_INDEX_COLUMNS:
                data.pop(k)

        (inserted, updated) = self.insert_update_one_exclude('file_index',
                                                             exclude_on_update=[
                                                                 'indexing_date',
                                                                 'created',
                                                                 'last_accessed',
                                                                 'last_modified',
                                                                 'filename',
                                                                 'extension',
                                                                 'integrated',
                                                                 'data',
                                                                 'index_id'
                                                             ],
                                                             **data)

        dt = self.select_first('file_index', fingerprint=data['fingerprint'])
        if dt is None:
            return None

        dt.update(dict(inserted=inserted, updated=updated))

        return dt

    def insert_or_get_alert(self, **data) -> Optional[dict]:

        for k in [k1 for k1 in data.keys()]:
            if k not in self._ALERT_COLUMNS:
                data.pop(k)

        (inserted, updated) = self.insert_update_one_exclude('alert',
                                                             exclude_on_update=[
                                                                 'file_fingerprint',
                                                                 'data',
                                                                 'sent',
                                                                 'index_id'
                                                             ],
                                                             **data)

        dt = self.select_first('alert', fingerprint=data['fingerprint'])
        if dt is None:
            return None

        dt.update(dict(inserted=inserted, updated=updated))

        return dt

    def create_db(self):

        conn = self.connect_to_db(check=False)

        # definindo um cursor
        cursor = conn.cursor()

        # criando a tabela (schema)
        cursor.execute("""
                    CREATE TABLE IF NOT EXISTS [index] (
                        index_id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT NOT NULL,
                        create_date datetime NOT NULL DEFAULT (datetime('now','localtime')),
                        UNIQUE(name)
                    );
                """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS [file_index] (
                file_id INTEGER PRIMARY KEY AUTOINCREMENT,
                index_id INTEGER NOT NULL,
                fingerprint TEXT NOT NULL,
                filename TEXT NOT NULL,
                file_size INTEGER,
                extension TEXT NOT NULL,
                mime_type TEXT NOT NULL,
                created datetime NOT NULL,
                last_accessed datetime NOT NULL,
                last_modified datetime NOT NULL,
                indexing_date datetime NOT NULL,
                path_real TEXT NOT NULL,
                path_virtual TEXT NOT NULL,
                data TEXT NULL,
                integrated INTEGER NOT NULL DEFAULT (0),
                FOREIGN KEY(index_id) REFERENCES [index](index_id),
                UNIQUE(index_id, fingerprint)
            );
        """)
        conn.commit()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS [alert] (
                alert_id INTEGER PRIMARY KEY AUTOINCREMENT,
                index_id INTEGER NOT NULL,
                file_fingerprint TEXT NOT NULL,
                fingerprint TEXT NOT NULL,
                data TEXT NULL,
                sent INTEGER NOT NULL DEFAULT (0),
                FOREIGN KEY(index_id) REFERENCES [index](index_id),
                UNIQUE(index_id, fingerprint)
            );
        """)
        conn.commit()

        cursor.execute("""
                    CREATE INDEX idx_file_index_fingerprint
                    ON [file_index] (fingerprint);
                """)

        conn.commit()

        cursor.execute("""
                    CREATE INDEX idx_file_index_file_id
                    ON [file_index] (file_id);
                """)

        conn.commit()

        cursor.execute("""
                    CREATE INDEX idx_file_index_integrated
                    ON [file_index] (integrated);
                """)

        conn.commit()

        cursor.execute("""
                    CREATE INDEX idx_file_index_integrated_indexing_date
                    ON [file_index] (integrated, indexing_date);
                """)

        conn.commit()

        #Must get the constraints
        self.get_constraints()
