import json

import xmltodict

from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class XMLParser(ParserBase):
    extensions = ['xml']
    mime_types = ['text/xml']

    def __init__(self):
        super().__init__('XML Parser', 'Parser for XML files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        data = {'content': self.get_readable_data(file)}

        if Configuration.xml_support:
            try:
                with open(file.path, 'r') as xml_file:
                    data_dict = xmltodict.parse(xml_file.read())
                    data['object_content'] = json.loads(data_dict)
            except:
                pass

        return data

    def parse_from_bytes(self, file_data: bytes) -> dict:
        from filecrawler.config import Configuration
        data = {'content': self.get_readable_data(file_data)}

        if Configuration.xml_support:
            try:
                data_dict = xmltodict.parse(file_data)
                data['object_content'] = json.loads(data_dict)
            except:
                pass

        return data

