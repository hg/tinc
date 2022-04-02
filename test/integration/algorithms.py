#!/usr/bin/env python3

from testlib import Tinc, log, cmd


def init(digest: str, cipher: str) -> (Tinc, Tinc):
    foo, bar = Tinc(), Tinc()

    foo.cmd(stdin=f'''
        init {foo.name}
        set Port {foo.port}
        set DeviceType dummy
        set Address localhost
        set ExperimentalProtocol no
    ''')

    bar.cmd(stdin=f'''
        init {bar.name}
        set Port 0
        set DeviceType dummy
        set ExperimentalProtocol no
        set Digest {digest}
        set Cipher {cipher}
    ''')

    foo.add_script(bar.script_up)
    bar.add_script(foo.script_up)

    cmd.exchange(foo, bar)
    bar.cmd('add', 'ConnectTo', foo.name)

    return foo, bar


for digest in ['none', 'sha256', 'sha512']:
    for cipher in ['none', 'aes-256-cbc']:
        log.info('testing combination %s %s', digest, cipher)

        foo, bar = init(digest, cipher)

        foo.cmd('start')
        bar.cmd('start')

        log.info('waiting for bar to come up')
        foo[bar.script_up].wait()

        log.info('waiting for foo to come up')
        bar[foo.script_up].wait()

        stdout, _ = foo.cmd('info', bar.name)
        assert 'reachable' in stdout

        bar.cmd('stop')
        foo.cmd('stop')
