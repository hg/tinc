#!/usr/bin/env python3

import subprocess as subp

from testlib import log, path, check

for p in (
        path.tinc_path,
        path.tincd_path,
        path.sptps_test_path,
        path.sptps_keypair_path,
):
    cmd = [p, '--help']
    log.info('testing command "%s"', cmd)
    res = subp.run(cmd, stdout=subp.PIPE, stderr=subp.PIPE, encoding='utf-8')
    check.equals(0, res.returncode)
    check.in_('Usage:', res.stdout, res.stderr)
