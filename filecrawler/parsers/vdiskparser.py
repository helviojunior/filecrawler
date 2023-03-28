from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class VDiskParser(ParserBase):
    extensions = ['vmdk', 'vhd', 'vhdx']
    mime_types = []

    def __init__(self):
        super().__init__('Virtual Disk Parser', 'Parser for Virtual Disk files')

    def parse(self, file: File) -> dict:
        data = {'content': ''}

        #TODO: Implementar

        return data

