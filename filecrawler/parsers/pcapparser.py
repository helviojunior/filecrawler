from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class PcapParser(ParserBase):
    extensions = ['pcap', 'pcapx']
    mime_types = ['application/vnd.tcpdump.pcap']

    def __init__(self):
        super().__init__('PCAP Parser', 'Parser for PCAP files')

    def parse(self, file: File) -> dict:
        data = {'content': ''}

        #TODO: Parse PCAP files

        return data
