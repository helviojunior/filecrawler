import json

import yaml

from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class YamlParser(ParserBase):
    extensions = ['yml', 'yaml']
    mime_types = []

    def __init__(self):
        super().__init__('YAML Parser', 'Parser for YAML files')

    def parse(self, file: File) -> dict:
        data = {'content': self.get_readable_data(file)}

        try:
            with open(file.path, 'r') as f:
                tmp = dict(yaml.load(f, Loader=yaml.FullLoader))
                data['object_content'] = json.dumps(tmp, sort_keys=False, indent=2)
        except:
            pass

        return data

    def parse_from_bytes(self, file_data: bytes) -> dict:
        data = {'content': self.get_readable_data(file_data)}

        try:
            tmp = dict(yaml.load(file_data, Loader=yaml.FullLoader))
            data['object_content'] = json.dumps(tmp, sort_keys=False, indent=2)
        except:
            pass

        return data



