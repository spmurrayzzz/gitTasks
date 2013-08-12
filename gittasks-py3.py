#!/usr/bin/env python3

import argparse
import datetime
from datetime import datetime
import hashlib
import json
import os
# import pytz
import re
import sys


if __name__ == '__main__':
    # Parser
    parser = argparse.ArgumentParser(
        formatter_class=argparse.RawDescriptionHelpFormatter,
        prog='gittasks-py3.py',
        description='''
    A to-do list.
        ''',
        epilog='''
    See 'gittasks-py3.py help <command>' for more information on a specific command.
        ''')

    parser.add_argument(
        'cmd',
        nargs='*',
        help=argparse.SUPPRESS
    )

    opts = vars(parser.parse_args())
    command = opts.pop('cmd')
