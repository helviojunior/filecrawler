import base64
import datetime
import json
import re
from typing import Optional

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

    def post_processor(self, original_data: str, found: str) -> dict:
        try:
            parts = found.split('.')
            if len(parts) >= 2:
                payload = json.loads(base64.b64decode(parts[1] + '=' * (-len(parts[1]) % 4)).decode("utf-8"))
                exp = int(payload.get('exp', 0))
                exp_date = None

                try:
                    exp_date = datetime.datetime.fromtimestamp(exp)
                except:
                    pass

                return dict(
                    header=json.loads(base64.b64decode(parts[0] + '=' * (-len(parts[0]) % 4)).decode("utf-8")),
                    payload=payload,
                    exp_date=exp_date,
                    still_valid=exp >= (datetime.datetime.utcnow().timestamp() + 10080),
                    severity=80 if exp >= (datetime.datetime.utcnow().timestamp() + 10080) else 10
                )
            else:
                return {}
        except:
            return {}
