#!/usr/bin/env python3

import os

from testlib import Script, Tinc, log


def init() -> Tinc:
    node = Tinc()
    node.add_script(Script.TINC_UP)
    node.cmd(stdin=f'''
        init {node.name}
        set DeviceType dummy
        set Port 0
    ''')
    return node


for code, flags in (
        (0, ['-D']),
        (0, ['--no-detach']),
        (0, ['-D', '-d']),
        (0, ['-D', '-d2']),
        (0, ['-D', '-d', '2']),
        (0, ['-D', '-n', 'foo']),
        (0, ['-D', '-nfoo']),
        (0, ['-D', '--net=foo']),
        (0, ['-D', '--net', 'foo']),
        (0, ['-D', '-c', '.', '-c', '.']),
        (0, ['-D', '-n', 'net', '-n', 'net']),
        (0, ['-D', '-n', 'net', '-o', 'FakeOpt=42']),
        (0, ['-D', '--logfile=log', '--logfile=log']),
        (0, ['-D', '--pidfile=pid', '--pidfile=pid']),
        (1, ['foo']),
        (1, ['--pidfile']),
        (1, ['--foo']),
        (1, ['-n', 'net', '-o', 'Compression=']),
        (1, ['-c', 'fakedir', '-n', 'n/e\\t']),
):
    node = init()
    cmd = node.tincd(*flags)

    if not code:
        node[Script.TINC_UP].wait()

    node.cmd('stop', code=code)

    stdout, stderr = cmd.communicate()
    log.debug('got code %d, stdout "%s", stderr "%s"', cmd.returncode, stdout, stderr)

    assert cmd.returncode == code

for code, flags in (
        (0, ['get', 'name']),
        (0, ['-n', 'foo', 'get', 'name']),
        (0, ['-nfoo', 'get', 'name']),
        (0, ['--net=foo', 'get', 'name']),
        (0, ['--net', 'foo', 'get', 'name']),
        (0, ['-c', 'conf', '-c', 'conf']),
        (0, ['-n', 'net', '-n', 'net']),
        (0, ['--pidfile=pid', '--pidfile=pid']),
        (1, ['-n', 'foo', 'get', 'somethingreallyunknown']),
        (1, ['--net']),
        (1, ['--net', 'get', 'name']),
        (1, ['foo']),
        (1, ['-c', 'conf', '-n', 'n/e\\t']),
):
    node = init()
    node.cmd(*flags, code=code)
