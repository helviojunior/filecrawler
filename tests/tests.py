#reference: https://medium.com/assertqualityassurance/tutorial-de-pytest-para-iniciantes-cbdd81c6d761
import codecs
import os.path

import sys

import yaml

from filecrawler.filecrawler import FileCrawler, Configuration
from filecrawler.libs.color import Color


def test_001_create_config():
    sys.argv = ['filecrawler', '-vvv', '--create-config']
    if sys.stdout.encoding is None:
        # Output is redirected to a file
        sys.stdout = codecs.getwriter('latin-1')(sys.stdout)

    try:

        if os.path.isfile('config.yml'):
            os.unlink('config.yml')

        o = FileCrawler()
        o.print_banner()

        o.dependency_check()

        Configuration.initialize()

        #o.main()

        assert True
    except Exception as e:
        Color.pl('\n{!} {R}Error:{O} %s{W}' % str(e))

        Color.pl('\n{!} {O}Full stack trace below')
        from traceback import format_exc
        Color.p('\n{!}    ')
        err = format_exc().strip()
        err = err.replace('\n', '\n{W}{!} {W}   ')
        err = err.replace('  File', '{W}{D}File')
        err = err.replace('  Exception: ', '{R}Exception: {O}')
        Color.pl(err)

        assert False


def test_002_change_config():
    try:

        with open('config.yml', 'r') as f:
            data = dict(yaml.load(f, Loader=yaml.FullLoader))
            data['general']['continue_on_error'] = False

        with open('config.yml', 'w') as f:
            yaml.dump(data, f, sort_keys=False, default_flow_style=False)

        assert True

    except Exception as e:
        Color.pl('\n{!} {R}Error:{O} %s{W}' % str(e))

        Color.pl('\n{!} {O}Full stack trace below')
        from traceback import format_exc
        Color.p('\n{!}    ')
        err = format_exc().strip()
        err = err.replace('\n', '\n{W}{!} {W}   ')
        err = err.replace('  File', '{W}{D}File')
        err = err.replace('  Exception: ', '{R}Exception: {O}')
        Color.pl(err)

        assert False

def test_003_run_local():
    sys.argv = ['filecrawler', '-vvv', '--index-name', 'test', '--path', '.', '--local', '-o', '/tmp']
    if sys.stdout.encoding is None:
        # Output is redirected to a file
        sys.stdout = codecs.getwriter('latin-1')(sys.stdout)

    try:

        o = FileCrawler()
        o.print_banner()

        o.main()

        assert True

    except Exception as e:
        Color.pl('\n{!} {R}Error:{O} %s{W}' % str(e))

        Color.pl('\n{!} {O}Full stack trace below')
        from traceback import format_exc
        Color.p('\n{!}    ')
        err = format_exc().strip()
        err = err.replace('\n', '\n{W}{!} {W}   ')
        err = err.replace('  File', '{W}{D}File')
        err = err.replace('  Exception: ', '{R}Exception: {O}')
        Color.pl(err)

        assert False

