from re import Pattern
from typing import Iterator


class Alert(object):
    _id = ''
    _name = ''
    _alert = ''
    _qualname = ''
    _class = None
    _config = {}

    def __init__(self, id: str, name: str, alert: str, qualname: str, class_name: type, config: dict):
        self._id = id
        self._name = name
        self._alert = alert
        self._qualname = qualname
        self._class = class_name
        self._config = config

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def __str__(self):
        return f'<{self._name} id {self._id}>'

    def create_instance(self):
        return self._class(self._config)
