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

    def __init__(self, auto_create=True, db_name=None):

        if db_name is None:
            db_name = "filecrawler.db"

        super().__init__(
            auto_create=auto_create,
            db_name=db_name
        )

    def has_data(self) -> bool:
        return self.select_count('passwords') > 0

    def check_open(self) -> bool:
        return self.select_count('passwords') >= 0

    def insert_group(self, domain: int, object_identifier: str, name: str, dn: str = '', members: str = '',
                     membership: str = '') -> int:

        if domain == -1:
            raise Exception('Invalid domain')

        if object_identifier is None or object_identifier.strip() == '':
            raise Exception('object_identifier cannot be empty')

        #grp = self.select('groups',
        #                  object_identifier=object_identifier
        #                  )

        #if len(grp) == 0:
        #    self.insert_one('groups',
        self.insert_update_one('groups',
                               domain_id=domain,
                               name=name,
                               object_identifier=object_identifier,
                               dn=dn,
                               members=members,
                               membership=membership
                               )

    def update_password(self, password: Password, **kwargs):

        filter_data = {
            'ntlm_hash': password.ntlm_hash,
        }

        pwd = {
            'password': password.clear_text,
            'length': password.length,
            'entropy': password.entropy,
            'strength': password.strength,
            'upper': password.upper,
            'lower': password.lower,
            'digit': password.digit,
            'special': password.special,
            'latin': password.latin,
            'md5_hash': password.md5_hash,
            'sha1_hash': password.sha1_hash,
            'sha256_hash': password.sha256_hash,
            'sha512_hash': password.sha512_hash,
        }

        pwd.update(kwargs)

        self.update('passwords', filter_data, **pwd)

        # Get all credentials (user/computer) using this password
        credentials = self.select_raw(
            sql='select distinct c.credential_id, c.name, c.full_name, c.user_data_similarity from credentials as c '
                'inner join passwords as p on c.password_id = p.password_id '
                'where c.type = "U" '
                'and c.full_name != "" '
                'and p.ntlm_hash = ?',
            args=[password.ntlm_hash]
        )
        for c in credentials:
            names = [
                n.lower() for n in c['full_name'].split(' ')
                if len(n) > 3
            ]
            score = sorted(
                [password.calc_ratio(n) for n in names]
            )[-1]
            if int(c['user_data_similarity']) != int(score):
                self.update('credentials',
                            filter_data={'credential_id': c['credential_id']},
                            user_data_similarity=score
                            )

    def insert_password_manually(self, password: Password, **kwargs):

        self.insert_ignore_one('pre_computed',
                               ntlm_hash=password.ntlm_hash,
                               password=password.clear_text if password.length > 0 else ''
                               )

        self.update_password(password, **kwargs)

        self.insert_update_one('pre_computed',
                               ntlm_hash=password.ntlm_hash,
                               md5_hash=password.md5_hash,
                               sha1_hash=password.sha1_hash,
                               sha256_hash=password.sha256_hash,
                               sha512_hash=password.sha512_hash,
                               password=password.clear_text,
                               )

    def insert_or_update_bloodhound_object(self, label: str, object_id: str, filter_type: str = 'objectid',  **props):

        object_id = object_id.upper()

        name = props.get('name', '')
        domain = props.get('domain', '').upper()
        name = name.replace(f'@{domain}', '').replace(f'.{domain}', '')

        rid = ''
        if object_id[0:2] == "S-" and \
                (label.lower() == 'group' or label.lower() == 'user' or label.lower() == 'machine'):
            rid = object_id.split('-')[-1]

        self.insert_update_one(
            'bloodhound_objects',
            object_id=object_id,
            filter_type=filter_type,
            object_label=label,
            name=name,
            r_id=rid,
            props=json.dumps(props)
        )

    def insert_or_update_bloodhound_edge(self, source: str, target: str, source_label: str, target_label: str,
                                         edge_type: str, edge_props: str, filter_type: str = 'objectid',
                                         props: dict = {}):

        txt_props = json.dumps(props)
        checksum = hashlib.md5(
            f'{source_label}:{target_label}:{edge_type}:{source}:{target}:{txt_props}'.encode("UTF-8")
        ).hexdigest().lower()

        self.insert_update_one(
            'bloodhound_edge',
            edge_id=checksum,
            source_id=source,
            destination_id=target,
            edge_props=edge_props,
            source_label=source_label,
            target_label=target_label,
            edge_type=edge_type,
            source_filter_type=filter_type,
            updated_date=datetime.datetime.utcnow(),
            props=txt_props
        )

    def insert_or_update_credential(self, domain: int, username: str, ntlm_hash: str,
                                    dn: str = '', groups: str = '', object_identifier: str = '',
                                    type: str = 'U', full_name: str = '', enabled: bool = True,
                                    pwd_last_set: datetime.datetime = datetime.datetime(1970, 1, 1, 0, 0, 0, 0)):
        try:

            # Hard-coded empty password
            update_password = True
            if ntlm_hash is None or ntlm_hash.strip == '':
                update_password = False
                ntlm_hash = '31d6cfe0d16ae931b73c59d7e0c089c0'

            passwd = self.select_first('passwords', ntlm_hash=ntlm_hash)
            password_id = -1 if passwd is None else passwd['password_id']

            if password_id == -1:
                self.insert_one('passwords', domain_id=domain, ntlm_hash=ntlm_hash)

                passwd = self.select_first('passwords', ntlm_hash=ntlm_hash)
                password_id = -1 if passwd is None else passwd['password_id']

            if password_id == -1:
                raise Exception('Password not found at database')

            data = {
                'domain_id': domain,
                'name': username,
                'type': type,
                'enabled': enabled,
                'password_id': password_id
            }
            if full_name is not None:
                data['full_name'] = full_name
            if dn is not None:
                data['dn'] = dn
            if groups is not None:
                data['groups'] = groups
            if object_identifier is not None:
                data['object_identifier'] = object_identifier
            if pwd_last_set is not None and pwd_last_set.year > 1970:
                data['pwd_last_set'] = pwd_last_set

            self.insert_update_one_exclude('credentials',
                                           exclude_on_update=['password_id'] if not update_password else [],
                                           **data)

        except Exception as e:
            Color.pl('{!} {R}Error inserting credential data:{O} %s{W}' % str(e))
        pass

    def insert_or_get_index(self, index_name: str) -> int:

        if index_name is None or index_name.strip() == '':
            raise Exception('Domain cannot be empty')

        f = {
            'name': index_name.lower()
        }

        self.insert_update_one_exclude('index', **f)

        return self.select_first('index', **f).get('index_id', -1)

    def insert_or_get_file(self, **data) -> Optional[dict]:

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



