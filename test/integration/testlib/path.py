#!/usr/bin/env python3

import os
import pathlib
import sys

python_path = os.getenv('PYTHON_PATH')
test_name = os.getenv('TEST_NAME')
tinc_path = os.getenv('TINC_PATH')
tincd_path = os.getenv('TINCD_PATH')
sptps_test_path = os.getenv('SPTPS_TEST_PATH')
sptps_keypair_path = os.getenv('SPTPS_KEYPAIR_PATH')
splice_path = os.getenv('SPLICE_PATH')

if not test_name \
        or not python_path or not os.path.isfile(python_path) \
        or not tinc_path or not os.path.isfile(tinc_path) \
        or not tincd_path or not os.path.isfile(tincd_path):
    print('Please run tests via meson or ninja')
    sys.exit(1)

# Current working directory
cwd = os.getcwd()

# Working directory for this test
test_wd = os.path.join(cwd, 'wd', test_name)

# Source root for the integration test suite
test_src_root = pathlib.Path(__file__).parent.parent.resolve()
