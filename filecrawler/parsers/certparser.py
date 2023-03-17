import json
import sys
from pathlib import Path

from filecrawler.libs.file import File
from filecrawler.libs.parser import Parser
from filecrawler.util.color import Color
from filecrawler.util.logger import Logger
from filecrawler.parserbase import ParserBase


class CertificateParser(ParserBase):
    extensions = ['p8', 'key', 'p10', 'csr', 'cer', 'crl', 'p7c', 'crt', 'der', 'pem',
                  'p12', 'pfx', 'p7b', 'spc', 'p7r']

    def __init__(self):
        super().__init__('Certificate Parser', 'Parser for Certificate files')

    def parse(self, file: File) -> dict:
        from filecrawler.config import Configuration
        from OpenSSL import crypto

        '''        
        PKCS#8 private keys
        PKCS#10 CSRs
        X.509 certificates
        X.509 CRLs
        PKCS#7 bundles of two or more certificates
        PKCS#12 bundles of private key + certificate(s)
        '''

        data = {'content': self.get_readable_data(file)}

        bData = file.path.read_bytes()
        cert = None
        try:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, bData)
        except:
            try:
                cert = crypto.load_certificate(crypto.FILETYPE_ASN1, bData)
            except:
                pass

        if cert is not None:
            dmp = crypto.dump_certificate(crypto.FILETYPE_TEXT, cert).decode('utf-8')
            dmp += '\n'
            dmp += crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8')

            data['content'] = dmp

        return data


