import re

from filecrawler.rulebase import RuleBase


class AWS(RuleBase):

    def __init__(self):
        super().__init__('aws-access-token', 'AWS')

        self._regex = re.compile(r"(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}")
        self._keywords = ["AKIA",
                     "AGPA",
                     "AIDA",
                     "AROA",
                     "AIPA",
                     "ANPA",
                     "ANVA",
                     "ASIA",
                     ]
        self._exclude_keywords = [
            "EXAMPLE"  # AKIAIOSFODNN7EXAMPLE
        ]

        self._tps = [self.generate_sample_secret("AWS", "AKIALALEMEL33243OLIB")]
