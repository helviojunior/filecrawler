import re

from filecrawler.rulebase import RuleBase


class GitlabPat(RuleBase):

    def __init__(self):
        super().__init__('gitlab-pat', 'GitLab Personal Access Token')

        self._regex = re.compile(r'glpat-[0-9a-zA-Z\-\_]{20}')
        self._keywords = ["glpat-"]

        self._tps = [self.generate_sample_secret("gitlab", "glpat-%s" % self.new_secret(self.alpha_numeric(20)))]


class GitlabPipelineTriggerToken(RuleBase):

    def __init__(self):
        super().__init__('gitlab-ptt', 'GitLab Pipeline Trigger Token')

        self._regex = re.compile(r'glptt-[0-9a-f]{40}')
        self._keywords = ["glptt-"]

        self._tps = [self.generate_sample_secret("gitlab", "glptt-%s" % self.new_secret(self.hex(40)))]


class GitlabRunnerRegistrationToken(RuleBase):

    def __init__(self):
        super().__init__('gitlab-rrt', 'GitHub OAuth Access Token')

        self._regex = re.compile(r'GR1348941[0-9a-zA-Z\-\_]{20}')
        self._keywords = ["GR1348941"]

        self._tps = [self.generate_sample_secret("gitlab", "GR1348941%s" % self.new_secret(self.alpha_numeric(20)))]

