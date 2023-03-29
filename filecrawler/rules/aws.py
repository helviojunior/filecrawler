import re

from filecrawler.rulebase import RuleBase


class AWS(RuleBase):

    def __init__(self):
        super().__init__('aws-access-token', 'AWS')

        self._regex = re.compile(r"(?<![A-Z0-9])(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}")
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
        self._fp_regex = re.compile(r"[A-Z0-9]{1,3}(A3T[A-Z0-9]|AKIA|AGPA|AIDA|AROA|AIPA|ANPA|ANVA|ASIA)[A-Z0-9]{16}[A-Z0-9]{1,3}")

        self._tps = [self.generate_sample_secret("AWS", "AKIALALEMEL33243OLIB")]

    def post_processor(self, original_data: str, found: str) -> dict:
        try:
            p = re.compile(
                r"(?<![A-Za-z0-9/+=])[A-Za-z0-9/+=]{40}(?![A-Za-z0-9/+=])")

            pr = re.compile(r"(us(-gov)?|ap|ca|cn|eu|sa)-(central|(north|south)?(east|west)?)-\d")

            hex_p = re.compile(r"[a-fA-F0-9]+")

            start = original_data.find(found) - 200
            if start < 0:
                start = 0

            region = ""
            for m in pr.finditer(original_data, start):
                if m:
                    region = m[0]
                    break

            for m in p.finditer(original_data, start):
                if m:
                    if hex_p.sub('', m[0]).strip() != '': #Remove Hex values
                        return dict(
                            aws_access_key=found,
                            aws_access_secret=m[0],
                            aws_region=region,
                            severity=100
                        )

            return dict(
                        aws_access_key=found,
                        aws_region=region,
                        severity=30
                    )
        except Exception as e:
            return {}