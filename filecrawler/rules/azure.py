import re

from filecrawler.rulebase import RuleBase


class Azure(RuleBase):

    def __init__(self):
        super().__init__('azure-client-key', 'Azure Client Key')

        #TODO: azure_ad_client_id

        #self._secret_group = 1
        #self._regex = self.generate_semi_generic_regex(['adafruit'], self.alpha_numeric_extended_short("32"))
        #self._keywords = ["adafruit"]
