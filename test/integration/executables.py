#!/usr/bin/env python3

from subprocess import run, PIPE

from testlib import log, path, check

for exe in (
    path.tinc_path,
    path.tincd_path,
    path.sptps_test_path,
    path.sptps_keypair_path,
):
    cmd = [exe, "--help"]
    log.info('testing command "%s"', cmd)
    res = run(cmd, stdout=PIPE, stderr=PIPE, encoding="utf-8", timeout=10)
    check.equals(0, res.returncode)
    check.in_("Usage:", res.stdout, res.stderr)
