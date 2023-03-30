import re
import base64
import datetime
import json
from filecrawler.rulebase import RuleBase


class HttpAuthorizationHeader(RuleBase):

    def __init__(self):
        super().__init__('http-auth-header', 'HTTP Authorization Header')

        self._regex = re.compile(r"(?i)(Authorization|x-auth|x-token)[ ]{0,1}:[ ]{0,1}([a-za_z0-9]{1,50}) ([A-Za-z0-9/+=.-]+)")
        # (?![A-Za-z0-9:._-])
        self._keywords = ["Authorization"]
        self._fp_regex = re.compile(r"[a-zA-Z0-9_-]{2,30}://([<]{0,1})(user|username|usuario)([>]{0,1}):([<]{0,1})(pass|password|token|secret|senha)([>]{0,1})@")
        self._exclude_keywords = [
            "\n"  # Cannot exists break line
            "sqlserver://",
            "smtp://",
            "mailto:"
        ]

        self._tps = [
            self.generate_sample_secret("url", "Authorization: Bearer testeok\nnop"),
            self.generate_sample_secret("url", "Authorization:Token testeok"),
            self.generate_sample_secret("url", "Authorization: Basic dXNlcjpwYXNzMQ==")
        ]

    def post_processor(self, original_data: str, found: str) -> dict:
        try:
            p = re.compile(
                r"(?i)(.*):[ ]{0,1}([a-za_z0-9]{1,50}) ([A-Za-z0-9/+=.-]+)")

            severity = 100

            m = p.match(found)
            if not m:
                return {}

            auth_type = m.group(2)
            auth = m.group(3)
            data = dict(
                token=f'{auth_type} {auth}',
                severity=60
            )
            auth_type = auth_type.lower()
            try:
                if auth_type == 'jwt':
                    parts = found.split('.')
                    if len(parts) >= 2:
                        payload = json.loads(base64.b64decode(parts[1] + '=' * (-len(parts[1]) % 4)).decode("utf-8"))
                        exp = int(payload.get('exp', 0))
                        exp_date = None

                        try:
                            exp_date = datetime.datetime.fromtimestamp(exp)
                        except:
                            pass

                        data.update(dict(
                            header=json.loads(base64.b64decode(parts[0] + '=' * (-len(parts[0]) % 4)).decode("utf-8")),
                            payload=payload,
                            exp_date=exp_date,
                            still_valid=exp >= (datetime.datetime.utcnow().timestamp() + 10080),
                            severity=80 if exp >= (datetime.datetime.utcnow().timestamp() + 10080) else 10
                        ))

                elif auth_type == 'basic':
                    payload = base64.b64decode(auth).decode("utf-8")
                    parts = payload.split(':', 2)
                    if len(parts) == 2:
                        username = parts[0]
                        password = parts[1]

                        entropy = self.entropy(password)

                        if username.strip() == '' or password.strip() == '':
                            return {}

                        if entropy <= 0.7:
                            severity = 30

                        if entropy < 1.7:
                            severity = 65

                        if len(username) <= 2 or len(password) <= 2:
                            return {}

                        data.update(dict(
                            username=username,
                            password=password,
                            severity=severity,
                            entropy=entropy
                        ))

            except:
                pass
            finally:
                return data

        except:
            return {}
