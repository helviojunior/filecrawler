import re

from filecrawler.rulebase import RuleBase


class UrlCreds(RuleBase):

    def __init__(self):
        super().__init__('url-creds', 'URL Credentials')

        self._regex = re.compile(r"([a-zA-Z0-9_-]{2,30}://[^@:]{1,256}:[^@:/]{1,256}@[-a-zA-Z0-9:%._\\+~#?&//=]{2,256}\.[a-z]{2,6}[\.a-z]{0,6}[:0-9]{0,5})")
        self._keywords = ["://"]

        self._tps = [
            self.generate_sample_secret("url", "http://user:pass@domain.com.br:8080"),
            self.generate_sample_secret("url", "https://user:pass@domain.com:8080")
        ]
