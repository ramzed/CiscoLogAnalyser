# -*- coding:utf-8 -*-
"""
Вот такую красоту я люблю!
"""

import sys

from obfuscation import (
    MultiObfuscater,
    log,
    set_log_file
)


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]

    set_log_file('/tmp/obfuscate-debug.log', 'debug')

    log.info('New run. Hello everybody!')

    obfuscator = MultiObfuscater(input_file='dutylog',
                                 output_file='cleanlog')
    obfuscator.start()


if __name__ == '__main__':
    sys.exit(main())