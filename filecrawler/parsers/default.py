from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class DefaultParser(ParserBase):

    def __init__(self):
        super().__init__('Default', 'Default parser')

    def parse(self, file: File) -> dict:
        data = {'content': self.get_readable_data(file)}

        return data

    def parse_from_bytes(self, file_data: bytes) -> dict:
        data = {'content': self.get_readable_data(file_data)}

        return data
