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


class GitlabUrlToken(RuleBase):

    def __init__(self):
        super().__init__('gitlab-oauth-url', 'GitHub OAuth URL Access Token')

        self._regex = self._regex = re.compile(r"(http|https|ssh|git)://(oauth2|gitlab-ci-token):[^@:/\n\"' ]{16,256}@(?:(?:[a-zA-Z0-9-_]+\.)?[a-zA-Z_]+\.)?(gitlab)[a-zA-Z0-9._-]{0,256}[:0-9]{0,6}")
        self._keywords = ["://"]

        #/^[a-zA-Z0-9_.+-]+@(?:(?:[a-zA-Z0-9-]+\.)?[a-zA-Z]+\.)?(domain|domain2)\.com$/g

        self._tps = [
            self.generate_sample_secret("url", "https://oauth2:Sample-Fake_Token@gitlab.mycompany.cloud"),
            self.generate_sample_secret("url", "https://oauth2:Sample-Fake_Token@gitlab"),
            self.generate_sample_secret("url", "https://oauth2:Sample-Fake_Token@test.gitlab"),
            self.generate_sample_secret("url", "https://oauth2:Sample-Fake_Token@gitlab.com/teste"),
            self.generate_sample_secret("url", "https://oauth2:Sample-Fake_Token@gitlab.com:8080/teste"),
        ]

        self._fps = [
            self.generate_sample_secret("url", "https://oauth2:${GITLAB_TOKEN}@gitlab.mycompany.cloud"),
        ]

    def post_processor(self, original_data: str, found: str) -> dict:
        try:
            p = re.compile(
                r".*://(oauth2|gitlab-ci-token):([^@:/\n\"']{16,256})@((?:(?:[a-zA-Z0-9-_]+\.)?[a-zA-Z_]+\.)?(gitlab)[a-zA-Z0-9._-]{0,256}[:0-9]{0,6})")

            severity = 100

            m = p.match(found)
            if not m:
                return {}

            username = m.group(1)
            token = m.group(2)
            host = m.group(3)
            entropy = self.entropy(token)

            if token[0:1] == '$':
                severity = 70

            if entropy <= 0.7:
                severity = 30

            if entropy <= 1.5 and 'localhost' in found.lower():
                severity = 30

            return dict(
                username=username,
                token=token,
                host=host,
                severity=severity,
                entropy=entropy
            )

        except:
            return {}
