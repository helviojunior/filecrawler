#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import datetime
import sys, os.path
import sqlite3
import string, base64
import json
import hashlib
from sqlite3 import Connection, OperationalError, IntegrityError, ProgrammingError
from typing import Optional

from filecrawler.util.color import Color
from .database import Database
from filecrawler.password import Password


class CrawlerDB(Database):
    dbName = ""

    _FILE_INDEX_COLUMNS = ['file_id', 'index_id', 'fingerprint', 'filename', 'file_size', 'extension', 'mime_type',
                           'created', 'last_accessed', 'last_modified', 'indexing_date', 'path_real', 'path_virtual',
                           'data', 'integrated']

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



