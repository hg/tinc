#!/usr/bin/env python3

import logging
import os
import sys

from .path import test_wd, test_name

log_fmt = logging.Formatter('%(asctime)s %(name)s %(levelname)s %(message)s')

# Where to put log files for this test and nodes started by it
log_dir = os.path.join(test_wd, 'logs')

logging.basicConfig(level=logging.DEBUG)


def make_logger(name: str) -> logging.Logger:
    os.makedirs(log_dir, exist_ok=True)
    log = logging.getLogger(name)
    log.setLevel(logging.DEBUG)
    file = logging.FileHandler(os.path.join(log_dir, name + '.log'))
    file.setFormatter(log_fmt)
    log.addHandler(file)
    return log


# Main logger used by most tests
log = make_logger(test_name)

sys.excepthook = lambda *args: \
    log.error('Uncaught exception', exc_info=args)
