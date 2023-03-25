import re

from filecrawler.rulebase import RuleBase


class JWT(RuleBase):

    def __init__(self):
        super().__init__('jwt', 'JSON Web Token')

        self._secret_group = 1
        self._regex = self.generate_unique_token_regex(r'ey[0-9a-z]{30,34}\.ey[0-9a-z-\/_]{30,500}\.[0-9a-zA-Z-\/_]{10,200}={0,2}')
        self._keywords = ["ey"]

        self._tps = [
            'eyJhbGciOieeeiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwic3ViZSI6IjEyMzQ1Njc4OTAiLCJuYW1lZWEiOiJKb2huIERvZSIsInN1ZmV3YWZiIjoiMTIzNDU2Nzg5MCIsIm5hbWVmZWF3ZnciOiJKb2huIERvZSIsIm5hbWVhZmV3ZmEiOiJKb2huIERvZSIsInN1ZndhZndlYWIiOiIxMjM0NTY3ODkwIiwibmFtZWZ3YWYiOiJKb2huIERvZSIsInN1YmZ3YWYiOiIxMjM0NTY3ODkwIiwibmFtZndhZSI6IkpvaG4gRG9lIiwiaWZ3YWZhYXQiOjE1MTYyMzkwMjJ9.a_5icKBDo-8EjUlrfvz2k2k-FYaindQ0DEYNrlsnRG0==',
            'JWT = eyJhbGciOieeeiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwic3ViZSI6IjEyMzQ1Njc4OTAiLCJuYW1lZWEiOiJKb2huIERvZSIsInN1ZmV3YWZiIjoiMTIzNDU2Nzg5MCIsIm5hbWVmZWF3ZnciOiJKb2huIERvZSIsIm5hbWVhZmV3ZmEiOiJKb2huIERvZSIsInN1ZndhZndlYWIiOiIxMjM0NTY3ODkwIiwibmFtZWZ3YWYiOiJKb2huIERvZSIsInN1YmZ3YWYiOiIxMjM0NTY3ODkwIiwibmFtZndhZSI6IkpvaG4gRG9lIiwiaWZ3YWZhYXQiOjE1MTYyMzkwMjJ9.a_5icKBDo-8EjUlrfvz2k2k-FYaindQ0DEYNrlsnRG0'
        ]

