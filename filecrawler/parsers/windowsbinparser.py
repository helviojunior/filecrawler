from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class WindowsBinParser(ParserBase):
    extensions = ['exe', 'dll', 'ocx']
    mime_types = ['application/vnd.microsoft.portable-executable']

    def __init__(self):
        super().__init__('Windows Bin Parser', 'Parser for Windows Bin files')

    def parse(self, file: File) -> dict:
        data = {'content': ''}

        #TODO: Implementar parser
        # Extensoes conhecidas: .exe, .dll, .pyd, .ocx

        return data
