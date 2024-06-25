import base64
import datetime
import hashlib
import json
import os
import importlib
import pkgutil
import re
from pathlib import Path
from re import Pattern
from typing import Iterator, Optional, TypeVar

from filecrawler.libs.alert import Alert
from filecrawler.libs.rule import Rule
from filecrawler.libs.color import Color
from filecrawler.libs.logger import Logger

# case insensitive prefix
from filecrawler.util.tools import Tools

TAlertBase = TypeVar("TAlertBase", bound="AlertBase")


class AlertBase(object):
    _verbose = 0
    _id = ''
    _name = ''
    _config_sample = {}
    _min_severity = 70

    # Static
    _alerters = {}

    def __init__(self, id: str, name: str):
        self._name = name
        self._id = id

    def __str__(self):
        if self.__class__.__qualname__ == 'AlertBase':
            return f'<{self.__class__.__module__}.{self.__class__.__qualname__} object at 0x{id(self):x}>'

        return f'{self._name} <{self._id}>'

    def send_alert(self, match: str, indexing_date: datetime.datetime, rule: str,
                   filtered_file: str, content: str, severity: int, image_file: Path):
        pass

    def is_enabled(self) -> bool:
        return False

    @staticmethod
    def get_config_sample() -> dict:

        base_alerters = AlertBase.get_base_alert()

        base_path = os.path.join(
            Path(__file__).resolve().parent, 'alerts'
        )

        for loader, modname, ispkg in pkgutil.walk_packages([base_path]):
            if not ispkg:
                importlib.import_module(f'{base_alerters}.{modname}')

        return {
            t.id: t.config_sample
            for iclass in AlertBase.__subclasses__()
            if (t := iclass()) is not None
        }

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def min_severity(self) -> int:
        return self._min_severity

    @property
    def config_sample(self) -> dict:
        return self._config_sample

    @classmethod
    def get_base_alert(cls) -> str:
        file = Path(__file__).stem

        parent_module = f'.{cls.__module__}.'.replace(f'.{file}.', '').strip(' .')

        return '.'.join((parent_module, 'alerts'))

    @classmethod
    def load_alerters(cls, config: Optional[dict] = None, verbose: int = 0) -> dict:

        if AlertBase._alerters is not None and len(AlertBase._alerters) > 0:
            return AlertBase._alerters

        if config is None:
            return {}

        base_alerters = AlertBase.get_base_alert()

        alerters = {}

        base_path = os.path.join(
            Path(__file__).resolve().parent, 'alerts'
        )

        for loader, modname, ispkg in pkgutil.walk_packages([base_path]):
            if not ispkg:
                if verbose >= 2:
                    Color.pl('{?} Importing rule: %s' % f'{base_alerters}.{modname}')
                importlib.import_module(f'{base_alerters}.{modname}')

        if verbose:
            Logger.pl('')

        for iclass in AlertBase.__subclasses__():
            t = iclass(config)
            if t.id in alerters:
                raise Exception(f'Duplicated rule id [{t.id}]: {iclass.__module__}.{iclass.__qualname__}')

            if t.is_enabled():
                alerters[t.id] = Alert(
                    id=t.id,
                    name=t.name,
                    alert=str(iclass.__module__),
                    qualname=str(iclass.__qualname__),
                    class_name=iclass,
                    config=config
                )

        AlertBase._alerters = alerters
        return AlertBase._alerters

    @staticmethod
    def has_providers():
        if AlertBase._alerters is None or len(AlertBase._alerters) == 0:
            return False

        return True

    @staticmethod
    def alert(base_path: [str, Path], file_fingerprint: str, fingerprint: str, alert: dict):

        if base_path is None or file_fingerprint is None:
            return

        if AlertBase._alerters is None or len(AlertBase._alerters) == 0:
            return

        match = alert.get('match', None)
        indexing_date = alert.get('indexing_date', None)
        rule = alert.get('rule', None)
        filtered_file = alert.get('filtered_file', None)
        content = alert.get('content', None)
        severity = alert.get('severity', 0)

        if match is None:
            return

        image_name = Path(f'{base_path}/{file_fingerprint}.png').resolve()

        for _, a in AlertBase._alerters.items():
            inst = a.create_instance()
            inst.send_alert(
                match=match,
                indexing_date=indexing_date,
                rule=rule,
                filtered_file=filtered_file,
                content=content,
                severity=severity,
                image_file=image_name
            )
            del inst
