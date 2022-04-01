#!/usr/bin/env python3

import time

from testlib import Tinc, Script, log, cmd, check

foo, bar = Tinc(), Tinc()

foo.cmd(stdin=f'''
    init {foo.name}
    set DeviceType dummy
    set Port {foo.port}
    set Address localhost
    add Subnet 10.98.98.1
    set PingTimeout 2
''')

bar.cmd(stdin=f'''
    init {bar.name}
    set DeviceType dummy
    set Port 0
    add Subnet 10.98.98.2
    set PingTimeout 2
    set MaxTimeout 2
''')

foo.add_script(bar.script_up)
bar.add_script(foo.script_up)

cmd.exchange(foo, bar)

bar.cmd('add', 'ConnectTo', foo.name)


def run_test():
    foo.cmd('start')
    bar.cmd('start')

    foo[bar.script_up].wait()
    bar[foo.script_up].wait()

    check.nodes(foo, 2)
    check.nodes(bar, 2)

    bar.cmd('stop')
    foo.cmd('stop')

    foo_bar, _ = foo.cmd('get', f'{bar.name}.Ed25519PublicKey', code=None)
    log.info('got key foo/bar "%s"', foo_bar)

    bar_foo, _ = bar.cmd('get', f'{foo.name}.Ed25519PublicKey', code=None)
    log.info('got key bar/foo "%s"', bar_foo)

    return foo_bar, bar_foo


log.info('foo 1.1, bar 1.0')

bar.cmd('set', 'ExperimentalProtocol', 'no')
foo.cmd('del', f'{bar.name}.Ed25519PublicKey')
bar.cmd('del', f'{foo.name}.Ed25519PublicKey')

(foo_key, bar_key) = run_test()
assert not foo_key
assert not bar_key

log.info('foo 1.1, bar upgrades to 1.1')

bar.cmd('del', 'ExperimentalProtocol')

(foo_key, bar_key) = run_test()
assert foo_key
assert bar_key

log.info('bar downgrades, must not be allowed to connect')

bar.cmd('set', 'ExperimentalProtocol', 'no')

foo.add_script(Script.SUBNET_UP)
bar.add_script(Script.SUBNET_UP)

foo.cmd('start')
bar.cmd('start')

foo[Script.SUBNET_UP].wait()
bar[Script.SUBNET_UP].wait()

# no good way to wait for 'not connecting'
time.sleep(4)

check.nodes(foo, 1)
check.nodes(bar, 1)

foo.cmd('stop')
bar.cmd('stop')
