#!/usr/bin/env python3

import os.path
import typing as T

from testlib import Script, Tinc, log

foo, bar = Tinc(), Tinc()

subnet_foo = ('10.0.0.1', 'fec0::/64')
subnet_bar = ('10.0.0.2', 'fec0::/64#5')


def check_tinc(script: Script) -> None:
    log.info('checking tinc: %s', script)

    env = foo[script].wait()

    assert env['NETNAME'] == 'netname'
    assert env['NAME'] == foo.name
    assert env['DEVICE'] == 'dummy'


def check_subnet(script: Script, node: Tinc, subnet: str) -> None:
    log.info('checking subnet: %s %s %s', script, node, subnet)

    env = foo[script].wait()

    assert env['NETNAME'] == 'netname'
    assert env['NAME'] == foo.name
    assert env['DEVICE'] == 'dummy'
    assert env['NODE'] == node.name

    if node != foo:
        assert env['REMOTEADDRESS'] == '127.0.0.1'
        assert env['REMOTEPORT'] == str(node.port)

    if '#' in subnet:
        addr, weight = subnet.split('#')
        assert env['SUBNET'] == addr
        assert env['WEIGHT'] == weight
    else:
        assert env['SUBNET'] == subnet


def check_host(script: T.Union[Script, str]) -> None:
    log.info('checking host: %s', script)

    env = foo[script].wait()
    assert env['NETNAME'] == 'netname'
    assert env['NAME'] == foo.name
    assert env['DEVICE'] == 'dummy'
    assert env['NODE'] == bar.name
    assert env['REMOTEADDRESS'] == '127.0.0.1'
    assert env['REMOTEPORT'] == str(bar.port)


foo.cmd(stdin=f'''
    init {foo.name}
    set DeviceType dummy
    set Port {foo.port}
    set Address 127.0.0.1
    add Subnet {subnet_foo[0]}
    add Subnet {subnet_foo[1]}
''')

for script in (
        Script.TINC_UP,
        Script.TINC_DOWN,
        Script.HOST_UP,
        Script.HOST_DOWN,
        Script.SUBNET_UP,
        Script.SUBNET_DOWN,
        foo.script_up,
        foo.script_down,
        bar.script_up,
        bar.script_down,
        Script.INVITATION_CREATED,
        Script.INVITATION_ACCEPTED,
):
    foo.add_script(script)

log.info('start server')

foo.cmd('-n', 'netname', 'start')

check_tinc(Script.TINC_UP)

for sub in subnet_foo:
    check_subnet(Script.SUBNET_UP, foo, sub)

log.info('invite client')

url, _ = foo.cmd('-n', 'netname2', 'invite', bar.name)
url = url.strip()
env = foo[Script.INVITATION_CREATED].wait()

assert env['NETNAME'] == 'netname2'
assert env['NAME'] == foo.name
assert env['NODE'] == bar.name
assert env['INVITATION_URL'] == url
assert os.path.isfile(env['INVITATION_FILE'])

log.info('join client via url "%s"', url)

bar.cmd('-n', 'netname3', 'join', url)
env = foo[Script.INVITATION_ACCEPTED].wait()

assert env['NETNAME'] == 'netname'
assert env['NAME'] == foo.name
assert env['DEVICE'] == 'dummy'
assert env['NODE'] == bar.name
assert env['REMOTEADDRESS'] == '127.0.0.1'

log.info('start client')

bar.cmd(stdin=f'''
    set DeviceType dummy
    set Port {bar.port}
    add Subnet {subnet_bar[0]}
    add Subnet {subnet_bar[1]}
''')

bar.cmd('start')

check_host(Script.HOST_UP)
check_host(bar.script_up)

for sub in subnet_bar:
    check_subnet(Script.SUBNET_UP, bar, sub)

bar.cmd('stop')

check_host(Script.HOST_DOWN)
check_host(bar.script_down)

for sub in subnet_bar:
    check_subnet(Script.SUBNET_DOWN, bar, sub)

bar.cmd('start')

check_host(Script.HOST_UP)
check_host(bar.script_up)

for sub in subnet_bar:
    check_subnet(Script.SUBNET_UP, bar, sub)

log.info('stop server')

foo.cmd('stop')
bar.cmd('stop')

check_host(Script.HOST_DOWN)
check_host(bar.script_down)

for sub in subnet_bar:
    check_subnet(Script.SUBNET_DOWN, bar, sub)

for sub in subnet_foo:
    check_subnet(Script.SUBNET_DOWN, foo, sub)

check_tinc(Script.TINC_DOWN)
