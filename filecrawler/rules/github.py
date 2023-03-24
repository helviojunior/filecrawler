import re

from filecrawler.rulebase import RuleBase


class GitHubPat(RuleBase):

    def __init__(self):
        super().__init__('github-pat', 'GitHub Personal Access Token')

        self._regex = re.compile(r'ghp_[0-9a-zA-Z]{36}')
        self._keywords = ["ghp_"]

        self._tps = [self.generate_sample_secret("github", "ghp_%s" % self.new_secret(self.alpha_numeric(36)))]


class GitHubFineGrainedPat(RuleBase):

    def __init__(self):
        super().__init__('github-fine-grained-pat', 'GitHub Fine-Grained Personal Access Token')

        self._regex = re.compile(r'github_pat_[0-9a-zA-Z_]{82}')
        self._keywords = ["github_pat_"]

        self._tps = [self.generate_sample_secret("github", "github_pat_%s" % self.new_secret(self.alpha_numeric(82)))]


class GitHubOauth(RuleBase):

    def __init__(self):
        super().__init__('github-oauth', 'GitHub OAuth Access Token')

        self._regex = re.compile(r'gho_[0-9a-zA-Z]{36}')
        self._keywords = ["gho_"]

        self._tps = [self.generate_sample_secret("github", "gho_%s" % self.new_secret(self.alpha_numeric(36)))]


class GitHubApp(RuleBase):

    def __init__(self):
        super().__init__('github-app-token', 'GitHub App Token')

        self._regex = re.compile(r'(ghu|ghs)_[0-9a-zA-Z]{36}')
        self._keywords = ["ghu_", "ghs_"]

        self._tps = [
            self.generate_sample_secret("github", "ghu_%s" % self.new_secret(self.alpha_numeric(36))),
            self.generate_sample_secret("github", "ghs_%s" % self.new_secret(self.alpha_numeric(36)))
        ]


class GitHubRefresh(RuleBase):

    def __init__(self):
        super().__init__('github-refresh-token', 'GitHub Refresh Token')

        self._regex = re.compile(r'ghr_[0-9a-zA-Z]{36}')
        self._keywords = ["ghr_"]

        self._tps = [
            self.generate_sample_secret("github", "ghr_%s" % self.new_secret(self.alpha_numeric(36)))
        ]

