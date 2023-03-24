from re import Pattern
from typing import Iterator


class Rule(object):
    _id = ''
    _name = ''
    _rule = ''
    _qualname = ''
    _class = None

    def __init__(self, id: str, name: str, rule: str, qualname: str, class_name: type):
        self._id = id
        self._name = name
        self._rule = rule
        self._qualname = qualname
        self._class = class_name

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    def __str__(self):
        return f'<{self._name} id {self._id}>'

    def create_instance(self):
        return self._class()
