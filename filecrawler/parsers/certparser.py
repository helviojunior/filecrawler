from filecrawler.libs.file import File
from filecrawler.parserbase import ParserBase


class CertificateParser(ParserBase):
    extensions = ['p8', 'key', 'p10', 'csr', 'cer', 'crl', 'p7c', 'crt', 'der', 'pem',
                  'p12', 'pfx', 'p7b', 'spc', 'p7r']

    def __init__(self):
        super().__init__('Certificate Parser', 'Parser for Certificate files')

    def parse(self, file: File) -> dict:
        data = {'content': self.get_readable_data(file)}
        return self._parse(data, file.path.read_bytes())

    def parse_from_bytes(self, file_data: bytes) -> dict:
        data = {'content': self.get_readable_data(file_data)}
        return self._parse(data, file_data)

    def _parse(self, data: dict, content: bytes) -> dict:
        from OpenSSL import crypto

        '''        
        PKCS#8 private keys
        PKCS#10 CSRs
        X.509 certificates
        X.509 CRLs
        PKCS#7 bundles of two or more certificates
        PKCS#12 bundles of private key + certificate(s)
        '''

        cert = None
        try:
            cert = crypto.load_certificate(crypto.FILETYPE_PEM, content)
        except:
            try:
                cert = crypto.load_certificate(crypto.FILETYPE_ASN1, content)
            except:
                pass

        if cert is not None:
            dmp = crypto.dump_certificate(crypto.FILETYPE_TEXT, cert).decode('utf-8')
            dmp += '\n'
            dmp += crypto.dump_certificate(crypto.FILETYPE_PEM, cert).decode('utf-8')

            data['content'] = dmp

        return data
