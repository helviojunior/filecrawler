from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class PDFParser(ParserBase):
    extensions = ['pdf']

    def __init__(self):
        super().__init__('PDF Parser', 'Parser for PDF files')

    def parse(self, file: File) -> dict:
        data = self.ocr_file(file)

        return data
