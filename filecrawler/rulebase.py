import base64
import hashlib
import json
import os
import importlib
import pkgutil
import re
from pathlib import Path
from re import Pattern
from typing import Iterator, Optional, TypeVar

from filecrawler._exceptions import FalsePositiveError
from filecrawler.libs.rule import Rule
from filecrawler.libs.color import Color
from filecrawler.libs.logger import Logger

# case insensitive prefix
from filecrawler.util.tools import Tools

_CASE_INSENSITIVE = r'(?i)'

# identifier prefix (just an ignore group)
_IDENTIFIER_PREFIX = r'(?:'
# )(?:[0-9a-z\-_\t .]{0,20})(?:[\s|']|[\s|"]){0,3}
_IDENTIFIER_SUFFIX = base64.b64decode("KSg/OlswLTlhLXpcLV9cdCAuXXswLDIwfSkoPzpbXHN8J118W1xzfCJdKXswLDN9").decode(
    "UTF-8")

# commonly used assignment operators or function call
_OPERATOR = r'(?:=|>|:=|\|\|:|<=|=>|:)'

# boundaries for the secret
_SECRET_PREFIX_UNIQUE = r'\b('
# (?:'|\"|\s|=|\x60){0,5}(
_SECRET_PREFIX = base64.b64decode("KD86J3xcInxcc3w9fGApezAsNX0o").decode("UTF-8")
# )(?:['|\"|\n|\r|\s|`|;]|$)
_SECRET_SUFFIX = base64.b64decode("KSg/OlsnfFwifFxufFxyfFxzfGB8O118JCk=").decode("UTF-8")

TRuleBase = TypeVar("TRuleBase", bound="RuleBase")


class RuleBase(object):
    _verbose = 0
    _id = ''
    _name = ''

    # Overwritten by inherited class
    _regex = None
    _fp_regex = None
    _keywords = []
    _secret_group = 0
    _tps = []
    _fps = []
    _exclude_keywords = []
    _severity = 70

    # Static
    _rules = {}

    def __init__(self, id: str, name: str):
        self._name = name
        self._id = id

    def __str__(self):
        if self.__class__.__qualname__ == 'RuleBase':
            return f'<{self.__class__.__module__}.{self.__class__.__qualname__} object at 0x{id(self):x}>'

        return f'{self._name} <{self._id}>'

    def post_processor(self, original_data: str, found: str) -> dict:
        return {}

    @property
    def id(self) -> str:
        return self._id

    @property
    def name(self) -> str:
        return self._name

    @property
    def regex(self) -> Pattern:
        return self._regex

    @property
    def keywords(self) -> Iterator[str]:
        return self._keywords

    @classmethod
    def get_base_rule(cls) -> str:
        file = Path(__file__).stem

        parent_module = f'.{cls.__module__}.'.replace(f'.{file}.', '').strip(' .')

        return '.'.join((parent_module, 'rules'))

    @classmethod
    def list_rules(cls, verbose: int = 0) -> dict:

        if RuleBase._rules is not None and len(RuleBase._rules) > 0:
            return RuleBase._rules

        base_rules = RuleBase.get_base_rule()

        rules = {}

        base_path = os.path.join(
            Path(__file__).resolve().parent, 'rules'
        )

        for loader, modname, ispkg in pkgutil.walk_packages([base_path]):
            if not ispkg:
                if verbose >= 2:
                    Color.pl('{?} Importing rule: %s' % f'{base_rules}.{modname}')
                importlib.import_module(f'{base_rules}.{modname}')

        if verbose:
            Logger.pl('')

        for iclass in RuleBase.__subclasses__():
            if verbose >= 2:
                Color.pl('{?} Loading rule: %s' % f'{iclass.__module__}.{iclass.__qualname__}')
            try:
                t = iclass()
                if t.id in rules:
                    raise Exception(f'Duplicated rule id [{t.id}]: {iclass.__module__}.{iclass.__qualname__}')

                t.validate(verbose)

                rules[t.id] = Rule(
                    id=t.id,
                    name=t.name,
                    rule=str(iclass.__module__),
                    qualname=str(iclass.__qualname__),
                    class_name=iclass,
                )
            except Exception as e:
                from filecrawler.config import Configuration
                Color.pl('{!} {R}Error loading rule {O}%s{W}' % f'{iclass.__module__}.{iclass.__qualname__}')
                if Configuration.verbose >= 3:
                    Tools.print_error(e)
                if not Configuration.continue_on_error:
                    raise e

        RuleBase._rules = rules
        return RuleBase._rules

    def validate(self, verbose: int = 0):
        for tp in self._tps:
            r = self.run(tp)
            if verbose >= 2 and r is not None:
                Color.pl(('{?} {W}True positive OK for {O}%s{GR} \n'
                          '     Rule ID........: {G}%s{GR}\n'
                          '     True positive..: {G}%s{GR}\n'
                          '     Regexp.........: {G}%s{GR}\n'
                          '%s{W}\n') % (
                             self, self.id, tp, self.regex.pattern, ''.join([
                                 '     Result.........: {G}%s{GR}\n' % x for x in r])
                         ))
            if r is None:
                # Re-execute as verbose
                self.run(tp, verbose=True)

                raise Exception((f'Failed to validate. For rule ID [{self.id}], '
                                 f'true positive [{tp}] was not detected by regexp [{self.regex.pattern}]'))

        for fp in self._fps:
            r = self.run(fp)
            if verbose >= 2 and r is None:
                Color.pl(('{?} {W}False positive OK for {O}%s{GR} \n'
                          '     Rule ID........: {G}%s{GR}\n'
                          '     True positive..: {G}%s{GR}\n'
                          '     Regexp.........: {G}%s{W}\n') % (self.name, self.id, fp, self.regex.pattern))

            if r is not None:
                # Re-execute as verbose
                self.run(fp, verbose=True)
                raise Exception(f'Failed to validate (fp) [{self.id}]')

    @classmethod
    def detect(cls, text: str) -> Optional[dict]:
        '''
        Run rule defined by inherited class
        '''
        cls.list_rules()

        findings = {}
        for k, rule in cls._rules.items():
            inst = rule.create_instance()
            ret = inst.run(text)
            if ret is not None and len(ret) > 0:
                findings.update({inst.id: dict(name=str(inst), findings=ret)})
            del inst

        if len(findings) == 0:
            return None

        return dict(credentials=findings)

    @classmethod
    def generate_sample_secret(cls, identifier: str, secret: str) -> str:
        return '%s_filecrawler_secret = "%s"' % (identifier, secret)

    @classmethod
    def generate_semi_generic_regex(cls, identifiers, secret_regex: str) -> Pattern:
        txt = _CASE_INSENSITIVE
        txt += _IDENTIFIER_PREFIX
        txt += '|'.join(identifiers)
        txt += _IDENTIFIER_SUFFIX
        txt += _OPERATOR
        txt += _SECRET_PREFIX
        txt += secret_regex
        txt += _SECRET_SUFFIX

        return re.compile(txt)

    @classmethod
    def generate_unique_token_regex(cls, secret_regex: str) -> Pattern:
        txt = _CASE_INSENSITIVE
        txt += _SECRET_PREFIX_UNIQUE
        txt += secret_regex
        txt += _SECRET_SUFFIX

        return re.compile(txt)

    @classmethod
    def new_secret(cls, regex: Pattern) -> str:
        import exrex
        return exrex.getone(regex)

    @classmethod
    def numeric(cls, size: [str, int]):
        return r'[0-9]{%s}' % size

    @classmethod
    def hex(cls, size: [str, int]):
        return r'[a-f0-9]{%s}' % size

    @classmethod
    def alpha_numeric(cls, size: [str, int]):
        return r'[a-z0-9]{%s}' % size

    @classmethod
    def alpha_numeric_extended_short(cls, size: [str, int]):
        return r'[a-z0-9_-]{%s}' % size

    @classmethod
    def alpha_numeric_extended(cls, size: [str, int]):
        return r'[a-z0-9=_\-]{%s}' % size

    @classmethod
    def alpha_numeric_extended_long(cls, size: [str, int]):
        return r'[a-z0-9\/=_\+\-]{%s}' % size

    @classmethod
    def hex8_4_4_4_12(cls):
        return r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}'

    @classmethod
    def entropy(cls, data, unit='natural'):
        import math
        from collections import Counter
        base = {
            'shannon': 2.,
            'natural': math.exp(1),
            'hartley': 10.
        }

        if len(data) <= 1:
            return 0

        counts = Counter()

        for d in data:
            counts[d] += 1

        ent = 0

        probs = [float(c) / len(data) for c in counts.values()]
        for p in probs:
            if p > 0.:
                ent -= p * math.log(p, base[unit])

        return ent

    def run(self, text: str, verbose: bool = False) -> Optional[list]:
        # Pré filter
        if self._keywords is None or len(self._keywords) == 0:
            if verbose:
                Color.pl('{?} {W}Keywords array is empty found to {O}%s{W}\n' % self.id)
            return None

        if self._exclude_keywords is None:
            self._exclude_keywords = []

        if verbose:
            Color.pl('{?} {W}Keywords: {O}%s{W}\n' % ', '.join(self._keywords))

        l_text = text.lower()
        if not any([
            k for k in self._keywords
            if k.lower() in l_text
        ]):
            if verbose:
                Color.pl('{?} {W}None keywords found to {O}%s{W} at text {O}%s{W}\n' % (self.id, text))
            return None

        findings = []

        if self._regex is None and verbose:
            Color.pl('{?} {W}Regex is empty.\n')

        for f in self.run_regex(text, self._regex, verbose):
            if f is not None and f not in findings:
                ignore = next((True for x in self._exclude_keywords if x.lower() in f.lower()), False)
                if not ignore:
                    findings.append(f)

        if len(findings) == 0:
            return None

        try:
            fp = self.run_regex(text, self._fp_regex, verbose)
            if len(fp) > 0:
                findings = [
                    f for f in findings
                    if not any(
                        1 for fp1 in fp
                        if f in fp1
                    )
                ]

            findings = [
                f for f in findings
                if len(self.run_regex(f, self._fp_regex, verbose)) == 0
            ]

            if len(findings) == 0:
                return None

            findings = [
                p for f in findings
                if (p := self._post_processor(text, f)) is not None
            ]

            return findings

        except FalsePositiveError:
            return None

    def _post_processor(self, text: str, match: str) -> Optional[dict]:
        data = dict(match=match, severity=self._severity)
        mh = match
        try:
            data.update(self.post_processor(text, match))
        except FalsePositiveError as e:
            return None
        except:
            pass

        try:
            mh += json.dumps(data, default=Tools.json_serial)
        except:
            pass

        sha1sum = hashlib.sha1()
        sha1sum.update(mh.encode("utf-8"))
        data.update(dict(fingerprint=sha1sum.hexdigest()))
        return data

    def run_regex(self, text: str, regex: Pattern, verbose: bool = False) -> list:
        findings = []

        if regex is None:
            return findings

        for m in regex.finditer(text):
            if verbose:
                Color.pl('{?} {W}Match: {O}%s{W}\n' % m)
            f = None
            if self._secret_group == 0 and len(m.groups()) == 0:
                f = m[0]
            elif len(m.groups()) >= self._secret_group:
                f = m.group(self._secret_group)

            findings.append(f)

        return findings
