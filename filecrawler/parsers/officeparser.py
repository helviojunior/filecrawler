from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class OfficeParser(ParserBase):
    extensions = ['doc', 'docx', 'ppt', 'pptx', 'xls', 'xlsx', 'odt', 'xlsm', 'xltm', 'xlsb']
    mime_types = ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
                  'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
                  ]


    def __init__(self):
        super().__init__('Document Parser', 'Parser for Document files')

    def parse(self, file: File) -> dict:
        data = self.ocr_file(file)

        return data

