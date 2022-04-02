#!/usr/bin/env python3

import os
import pathlib
import sys

python_path = sys.executable
test_name = os.getenv('TEST_NAME')
tinc_path = os.getenv('TINC_PATH')
tincd_path = os.getenv('TINCD_PATH')
sptps_test_path = os.getenv('SPTPS_TEST_PATH')
sptps_keypair_path = os.getenv('SPTPS_KEYPAIR_PATH')
splice_path = os.getenv('SPLICE_PATH')

_paths = (
    python_path,
    tinc_path,
    tincd_path,
    sptps_test_path,
    sptps_keypair_path,
    splice_path,
)


def _check_path(path: str) -> bool:
    return path and os.path.isfile(path)


if not test_name or not all(map(_check_path, _paths)):
    print('Please run tests via meson or ninja')
    sys.exit(1)

# Current working directory
cwd = os.getcwd()

# Working directory for this test
test_wd = os.path.join(cwd, 'wd', test_name)

# Path to the Python test library
testlib_path = pathlib.Path(__file__).parent.resolve()

# Source root for the integration test suite
test_src_root = testlib_path.parent.resolve()
