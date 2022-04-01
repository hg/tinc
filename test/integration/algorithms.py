#!/usr/bin/env python3

from testlib import Tinc, log, cmd

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
''')

foo.add_script(bar.script_up)
bar.add_script(foo.script_up)

cmd.exchange(foo, bar)

bar.cmd('add', 'ConnectTo', foo.name)
foo.cmd('start')

for digest in ['none', 'sha256', 'sha512']:
    for cipher in ['none', 'aes-256-cbc']:
        log.info('testing combination %s %s', digest, cipher)

        bar.cmd(stdin=f'''
            set Digest {digest}
            set Cipher {cipher}
        ''')
        bar.cmd('start')

        log.info('waiting for bar to come up')
        foo[bar.script_up].wait()

        log.info('waiting for foo to come up')
        bar[foo.script_up].wait()

        stdout, _ = foo.cmd('info', bar.name)
        assert 'reachable' in stdout

        bar.cmd('stop')

foo.cmd('stop')
