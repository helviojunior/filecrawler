import re
from urllib.parse import unquote

from filecrawler._exceptions import FalsePositiveError
from filecrawler.rulebase import RuleBase


class Leaked1(RuleBase):

    def __init__(self):
        super().__init__('leaked1', 'Leaked Credentials 1')

        self._regex = re.compile(r"(?i)([a-zA-Z0-9_]+)[: ]{1,3}([a-zA-Z0-9_-]{2,30}:\/\/[^\"'\n]{1,1024})\n[ \t]{0,5}(user|username|login|email)[ :]{1,3}([^\n]{3,1024})\n[ \t]{0,5}(pass|password|token|secret|senha|pwd)[ :]{1,3}([^\n]{3,1024})", flags=re.RegexFlag.MULTILINE)
        # (?![A-Za-z0-9:._-])
        self._keywords = ["://"]
        #self._fp_regex = re.compile(r"[a-zA-Z0-9_-]{2,30}://([<]{0,1})(user|username|usuario)([>]{0,1}):([<]{0,1})(pass|password|token|secret|senha|pwd)([>]{0,1})@")
        self._exclude_keywords = [
        ]

        self._tps = [
            "URL: http://domain.com.br/login\nUSER: fake_user\nPASS: fake_pass"
        ]

        self._fps = [
            "Url: http://domain.com.br/login\nUSER: \nPASS: "
        ]

    def post_processor(self, original_data: str, found: str) -> dict:
        from urllib.parse import urlparse
        from filecrawler.config import Configuration
        try:
            p = re.compile(
                r"(?i)[a-zA-Z0-9_]{2,30}[: ]{1,3}([a-zA-Z0-9_-]{2,30}:\/\/[^\"'\n]{1,1024})\n[ \t]{0,5}[a-zA-Z0-9_]{2,30}[: ]{1,3}([^\n]{1,1024})\n[ \t]{0,5}[a-zA-Z0-9_]{2,30}[: ]{1,3}([^\n]{1,1024})", flags=re.RegexFlag.MULTILINE)

            severity = 100

            m = p.match(found.replace('\r', ''))
            if not m:
                return {}

            domain = None
            url = m.group(1)
            username = m.group(2)
            password = m.group(3)

            try:
                tmp = urlparse(url)
            except:
                # invalid URL
                return {}

            try:
                username = unquote(username)
            except:
                pass

            try:
                password = unquote(password)
            except:
                pass

            if '@' in username:
                pt = username.split('@', 2)
                if len(pt[1].strip()) > 3 and not pt[1].lower() in ['localhost', '127.0.0.1', 'example']:
                    domain = pt[1].lower()

            if '\\' in username:
                pt = username.split('\\', 2)
                if len(pt[0].strip()) > 3 and not pt[0].lower() in ['localhost', '127.0.0.1', 'example']:
                    domain = pt[0].lower()

            if domain is not None and any([
                True
                for d in Configuration.exclude_domains
                if d.lower() in domain.lower()
            ]):
                raise FalsePositiveError()

            entropy = self.entropy(password)

            if url.strip() == '' or password.strip() == '':
                return {}

            if password[0:1] == '$':
                severity = 60

            if entropy <= 0.7:
                severity = 30

            if entropy < 1.7:
                severity = 65

            if entropy <= 2 and '@localhost' in found.lower():
                severity = 30

            if entropy <= 2 and '@127.0.0.1' in found.lower():
                severity = 30

            if entropy <= 1.5 and 'example' in found.lower():
                severity = 30

            if len(username) <= 2 or len(password) <= 2:
                severity = 50

            if domain is not None and any([
                True
                for d in Configuration.public_domains
                if d.lower() in domain.lower()
            ]):
                severity -= 20

            return {
                **dict(
                    url=url,
                    username=username.strip('\r\n '),
                    password=password.strip('\r\n '),
                    severity=severity,
                    entropy=entropy
                ),
                **(dict(domain=domain.strip('\r\n ')) if domain is not None else {})
            }

        except FalsePositiveError as e:
            raise e

        except Exception as e:
            from filecrawler.util.tools import Tools
            Tools.print_error(e)
            return {}
