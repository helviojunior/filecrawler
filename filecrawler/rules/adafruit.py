import re

from filecrawler.rulebase import RuleBase


class AdafruitAPIKey(RuleBase):

    def __init__(self):
        super().__init__('adafruit-api-key', 'Adafruit API Key')

        self._secret_group = 1
        self._regex = self.generate_semi_generic_regex(['adafruit'], self.alpha_numeric_extended_short("32"))
        self._keywords = ["adafruit"]

        self._tps = [self.generate_sample_secret("adafruit", self.new_secret(self.alpha_numeric_extended_short("32")))]