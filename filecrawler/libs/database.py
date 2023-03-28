#!/usr/bin/python3
# -*- coding: UTF-8 -*-
import math
import shutil
import sys, os.path
import sqlite3
import string, base64
import time
from functools import reduce
from sqlite3 import Connection, OperationalError, IntegrityError, ProgrammingError
import contextlib


# TODO: use this decorator to wrap commit/rollback in a try/except block ?
# see http://www.kylev.com/2009/05/22/python-decorators-and-database-idioms/
def connect(func):
    """Decorator to (re)open a sqlite database connection when needed.

    A database connection must be open when we want to perform a database query
    but we are in one of the following situations:
    1) there is no connection
    2) the connection is closed

    Parameters
    ----------
    func : function
        function which performs the database query

    Returns
    -------
    inner func : function
    """

    def inner_func(self, *args, **kwargs):
        if f'{func.__module__}.{func.__qualname__}' != f'{Database.__module__}.{Database.__qualname__}.{func.__name__}':
            raise Exception('The connect decorator cannot be used outside of Database class')

        if not isinstance(self, Database):
            raise Exception('The connect decorator cannot be used outside of Database class')

        conn = kwargs.get('conn', None) if kwargs is not None else None
        if conn is None:
            conn = self.connect_to_db()

        try:
            with contextlib.closing(conn.cursor()) as cursor:
                pass
            #Connecion is open
        except:
            try:
                self.db_connection.close()
            except:
                pass
            self.db_connection = None
            conn = self.connect_to_db()

        return func(self, conn, *args, **kwargs)

    return inner_func


class Database(object):
    db_name = ""

    # Static value
    db_connection = None
    constraints = []

    def __init__(self, auto_create=True, db_name=None):

        self.db_name = db_name

        if not os.path.isfile(self.db_name):
            if auto_create:
                self.create_db()
            else:
                raise Exception("Database not found")
        else:
            self.connect_to_db()

    def __enter__(self):
        return self

    def __exit__(self, exception_type, exception_value, traceback):
        self.db_connection.close()

    def close(self):
        if self.db_connection is not None:
            self.db_connection.close()
        self.db_connection = None

    def reconnect(self):
        self.close()
        time.sleep(0.300)
        self.connect_to_db()

    @staticmethod
    def _execute(conn, sql, values):
        with conn:  # auto-commits
            with contextlib.closing(conn.cursor()) as cursor:  # auto-closes
                cursor.execute(sql, values)
                conn.commit()

    @connect
    def insert_one(self, conn, table_name, **kwargs):
        table_name = self.scrub(table_name)
        (columns, values) = self.parse_args(kwargs)
        sql = "INSERT INTO [{}] ({}) VALUES ({})" \
            .format(table_name, ','.join(columns), ', '.join(['?'] * len(columns)))
        Database._execute(conn, sql, values)

    @connect
    def insert_ignore_one(self, conn, table_name, **kwargs):
        table_name = self.scrub(table_name)
        (columns, values) = self.parse_args(kwargs)
        sql = "INSERT OR IGNORE INTO [{}] ({}) VALUES ({})" \
            .format(table_name, ','.join(columns), ', '.join(['?'] * len(columns)))
        Database._execute(conn, sql, values)

    @connect
    def insert_replace_one(self, conn, table_name, **kwargs):
        table_name = self.scrub(table_name)
        (columns, values) = self.parse_args(kwargs)
        sql = "INSERT OR REPLACE INTO [{}] ({}) VALUES ({})" \
            .format(table_name, ','.join(columns), ', '.join(['?'] * len(columns)))
        Database._execute(conn, sql, values)

    @connect
    def insert_update_one(self, conn: str, table_name: str, **kwargs):
        self.insert_update_one_exclude(table_name, [], **kwargs)

    @connect
    def insert_update_one_exclude(self, conn, table_name: str, exclude_on_update: list = [], **kwargs) -> (bool, bool):
        inserted = False
        updated = False
        table_name = self.scrub(table_name)
        (columns, values) = self.parse_args(kwargs)
        sql = "INSERT OR IGNORE INTO [{}] ({}) VALUES ({})" \
            .format(table_name, ','.join(columns), ', '.join(['?'] * len(columns)))
        with conn:  # auto-commits
            with contextlib.closing(conn.execute(sql, values)) as c:  # auto-closes

                # No inserted, need to update
                if c.rowcount == 0:
                    table_name = self.scrub(table_name)
                    f_columns = self.constraints[table_name]
                    f_values = tuple([kwargs.get(c, None) for c in f_columns],)
                    args = {k: v for k, v in kwargs.items() if k not in exclude_on_update}
                    (u_columns, u_values) = self.parse_args(args)

                    sql = f"UPDATE [{table_name}] SET "
                    sql += "{}".format(', '.join([f'{col} = ?' for col in u_columns]))
                    if len(f_columns) > 0:
                        sql += " WHERE {}".format(f' and '.join([f'{col} = ?' for col in f_columns]))
                    Database._execute(conn, sql, tuple(u_values + f_values, ))
                    updated = True
                else:
                    inserted = True

            conn.commit()
        return inserted, updated


    @connect
    def select(self, conn, table_name, **kwargs):

        operator = self.scrub(kwargs.get('__operator', 'and'))

        table_name = self.scrub(table_name)
        (columns, values) = self.parse_args(kwargs)

        sql = f"SELECT * FROM [{table_name}]"
        if len(columns) > 0:
            sql += " WHERE {}".format(f' {operator} '.join([f'{col} = ?' for col in columns]))

        with conn:  # auto-commits
            with contextlib.closing(conn.cursor()) as cursor:  # auto-closes
                cursor.execute(sql, values)

                if cursor.rowcount == 0:
                    return []

                columns = cursor.description
                return [{columns[index][0]: column for index, column in enumerate(value)} for value in cursor.fetchall()]

    def select_first(self, table_name, **kwargs):
        data = self.select(table_name, **kwargs)
        if len(data) == 0:
            return None
        return data[0]

    @connect
    def select_raw(self, conn, sql: str, args: any):
        with conn:  # auto-commits
            with contextlib.closing(conn.cursor()) as cursor:  # auto-closes
                cursor.execute(sql, tuple(args,))

                if cursor.rowcount == 0:
                    return []

                columns = cursor.description
                return [{columns[index][0]: column for index, column in enumerate(value)} for value in cursor.fetchall()]

    @connect
    def select_count(self, conn, table_name, **kwargs) -> int:

        operator = self.scrub(kwargs.get('__operator', 'and'))

        table_name = self.scrub(table_name)
        (columns, values) = self.parse_args(kwargs)

        sql = f"SELECT count(*) FROM [{table_name}]"
        if len(columns) > 0:
            sql += " WHERE {}".format(f' {operator} '.join([f'{col} = ?' for col in columns]))

        with conn:  # auto-commits
            with contextlib.closing(conn.cursor()) as cursor:  # auto-closes
                cursor.execute(sql, values)

                if cursor.rowcount == 0:
                    return 0

                data = cursor.fetchone()

                return int(data[0])

    @connect
    def delete(self, conn, table_name, **kwargs) -> None:

        operator = self.scrub(kwargs.get('__operator', 'and'))

        table_name = self.scrub(table_name)
        (columns, values) = self.parse_args(kwargs)

        sql = f"DELETE FROM [{table_name}]"
        if len(columns) > 0:
            sql += " WHERE {}".format(f' {operator} '.join([f'{col} = ?' for col in columns]))
        Database._execute(conn, sql, values)

    @connect
    def update(self, conn, table_name, filter_data, **kwargs):

        operator = self.scrub(kwargs.get('__operator', 'and'))

        table_name = self.scrub(table_name)
        (f_columns, f_values) = self.parse_args(filter_data)
        (u_columns, u_values) = self.parse_args(kwargs)

        sql = f"UPDATE [{table_name}] SET "
        sql += "{}".format(', '.join([f'{col} = ?' for col in u_columns]))
        if len(f_columns) > 0:
            sql += " WHERE {}".format(f' {operator} '.join([f'{col} = ?' for col in f_columns]))
        Database._execute(conn, sql, tuple(u_values + f_values, ))

    def get_constraints(self) -> dict:
        sql = ('SELECT '
               '  m.tbl_name AS table_name, '
               '  il.name AS key_name, '
               '  ii.name AS column_name '
               'FROM  '
               '  sqlite_master AS m,  '
               '  pragma_index_list(m.name) AS il,  '
               '  pragma_index_info(il.name) AS ii  '
               'WHERE  '
               '  m.type = "table" AND  '
               '  il.origin = "u"  '
               'ORDER BY table_name, key_name, ii.seqno')

        with self.db_connection:  # auto-commits
            with contextlib.closing(self.db_connection.cursor()) as cursor:  # auto-closes
                cursor.execute(sql)

                columns = cursor.description
                db_scheme = [{columns[index][0]: column for index, column in enumerate(value)} for value in cursor.fetchall()]

                if len(db_scheme) > 0:
                    self.constraints = reduce(lambda a, b: {**a, **b},
                                              [{table: [
                                                    v['column_name'] for idx, v in enumerate(db_scheme)
                                                    if v['table_name'] == table
                                                ]} for table in set([t['table_name'] for t in db_scheme])])
                else:
                    self.constraints = {}

                return self.constraints

    def parse_args(self, source_dict) -> tuple:
        if source_dict is None:
            return [], tuple([])

        if not isinstance(source_dict, dict):
            raise Exception('kwargs is not a dictionary')

        columns = []
        values = []

        for key, value in source_dict.items():
            try:
                if key[0:2] != '__':
                    columns.append(f"[{self.scrub(key)}]")
                    values.append(value)
            except Exception as e:
                raise Exception(f'Error parsing {key}: {value}', e)

        return columns, tuple(values, )

    def connect_to_db(self, check: bool = True) -> Connection:
        """Connect to a sqlite DB. Create the database if there isn't one yet.

        Open a connection to a SQLite DB (either a DB file or an in-memory DB).
        When a database is accessed by multiple connections, and one of the
        processes modifies the database, the SQLite database is locked until that
        transaction is committed.

        Returns
        -------
        connection : sqlite3.Connection
            connection object
        """

        if self.db_connection is not None:
            return self.db_connection

        conn = sqlite3.connect(self.db_name, detect_types=sqlite3.PARSE_DECLTYPES | sqlite3.PARSE_COLNAMES)
        conn.create_function('log', 2, math.log)

        if check:
            try:
                # I don't know if this is the simplest and fastest query to try
                with conn:  # auto-commits
                    with contextlib.closing(conn.cursor()) as cursor:  # auto-closes
                        cursor.execute('SELECT name FROM sqlite_temp_master WHERE type="table";')

            except (AttributeError, ProgrammingError) as e:
                raise Exception(f'Fail connecting to SQLite file: {self.db_name}', e)

        #shutil.copy(self.db_name, f'{self.db_name}.bkp')

        with conn:  # auto-commits
            with contextlib.closing(conn.cursor()) as cursor:  # auto-closes

                # www.sqlite.org/pragma.html
                # https://blog.devart.com/increasing-sqlite-performance.html
                cursor.execute("PRAGMA temp_store = MEMORY")
                # cursor.execute("PRAGMA page_size = 4096")
                # cursor.execute("PRAGMA cache_size = 10000")
                #cursor.execute("PRAGMA locking_mode=EXCLUSIVE")
                cursor.execute("PRAGMA synchronous=OFF")
                cursor.execute("PRAGMA busy_timeout=15000")  # milliseconds
                cursor.execute("PRAGMA lock_timeout=5000")  # milliseconds
                cursor.execute("PRAGMA journal_mode=MEMORY")

                # cursor.execute("PRAGMA foreign_keys=ON")

        self.db_connection = conn

        # get database constraints
        self.get_constraints()

        return self.db_connection

    def scrub(self, input_string):
        return Database.scrub(input_string)

    @staticmethod
    def scrub(input_string):
        """Clean an input string (to prevent SQL injection).

        Parameters
        ----------
        input_string : str

        Returns
        -------
        str
        """
        return ''.join(k for k in input_string if k.isalnum() or k in '_-')

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
