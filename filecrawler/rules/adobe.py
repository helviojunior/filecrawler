import re

from filecrawler.rulebase import RuleBase


class AdobeClientID(RuleBase):

    def __init__(self):
        super().__init__('adobe-client-id', 'Adobe Client ID (OAuth Web)')

        self._secret_group = 1
        self._regex = self.generate_semi_generic_regex(['adobe'], self.hex("32"))
        self._keywords = ["adobe"]

        self._tps = [self.generate_sample_secret("adobe", self.new_secret(self.hex("32")))]


class AdobeClientSecret(RuleBase):

    def __init__(self):
        super().__init__('adobe-client-secret', 'Adobe Client Secret')

        self._regex = self.generate_unique_token_regex(r'(p8e-)(?i)[a-z0-9]{32}')
        self._keywords = ["p8e-"]

        self._tps = ['adobeClient = "p8e-%s"' % self.new_secret(self.hex("32"))]

