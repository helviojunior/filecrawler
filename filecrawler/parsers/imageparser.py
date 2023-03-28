from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class ImageParser(ParserBase):
    extensions = ['png', 'jpg', 'jpeg', 'gif', 'emf']

    def __init__(self):
        super().__init__('Image Parser', 'Parser for Image files')

    def parse(self, file: File) -> dict:
        data = self.ocr_file(file)

        return data


