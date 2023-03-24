import re

from filecrawler.rulebase import RuleBase


class AgeSecretKey(RuleBase):

    def __init__(self):
        super().__init__('age-secret-key', 'Age secret key')

        self._regex = re.compile(r"AGE-SECRET-KEY-1[QPZRY9X8GF2TVDW0S3JN54KHCE6MUA7L]{58}")
        self._keywords = ["AGE-SECRET-KEY-1"]

        self._tps = ['apiKey = "AGE-SECRET-KEY-1QQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQQ"']
