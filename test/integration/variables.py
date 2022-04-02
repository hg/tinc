#!/usr/bin/env python3

from pathlib import Path

from testlib import Tinc, log, check

foo, bar = Tinc(), Tinc()


def get(tinc: Tinc, var: str) -> str:
    stdout, _ = tinc.cmd('get', var)
    return stdout.strip()


log.info('initialize node %s', foo.name)

foo.cmd('init', foo.name)
check.equals(foo.name, get(foo, 'Name'))

log.info('test case sensitivity')

foo.cmd('set', 'Mode', 'switch')
check.equals('switch', get(foo, 'Mode'))
check.equals('switch', get(foo, 'mOdE'))

foo.cmd('set', 'Mode', 'router')
check.equals('router', get(foo, 'MoDE'))
check.equals('router', get(foo, 'mode'))

foo.cmd('set', 'Mode', 'Switch')
check.equals('Switch', get(foo, 'mode'))

log.info('test deletion')

foo.cmd('del', 'Mode', 'hub', code=1)
foo.cmd('del', 'Mode', 'switch')

mode, _ = foo.cmd('get', 'Mode', code=1)
check.false(mode)

log.info('there can only be one Mode variable')

foo.cmd('add', 'Mode', 'switch')
foo.cmd('add', 'Mode', 'hub')
check.equals('hub', get(foo, 'Mode'))

log.info('test addition/deletion of multivalued variables')

for i in range(1, 4):
    sub = f'{i}.{i}.{i}.{i}'
    foo.cmd('add', 'Subnet', sub)
    foo.cmd('add', 'Subnet', sub)

check.equals(['1.1.1.1', '2.2.2.2', '3.3.3.3'],
             get(foo, 'Subnet').splitlines())

log.info('delete one subnet')

foo.cmd('del', 'Subnet', '2.2.2.2')
check.equals(['1.1.1.1', '3.3.3.3'],
             get(foo, 'Subnet').splitlines())

log.info('delete all subnets')

foo.cmd('del', 'Subnet')

subnet, _ = foo.cmd('get', 'Subnet', code=1)
check.false(subnet)

log.info('we should not be able to get/set server variables using node.variable syntax')

name, _ = foo.cmd('get', f'{foo.name}.Name', code=1)
check.false(name)

foo.cmd('set', f'{foo.name}.Name', 'fake', code=1)

log.info('test getting/setting host variables for other nodes')

foo_bar = foo.sub('hosts', bar.name)
Path(foo_bar).touch(0o644, exist_ok=True)

bar_pmtu = f'{bar.name}.PMTU'
foo.cmd('add', bar_pmtu, '1')
foo.cmd('add', bar_pmtu, '2')
check.equals('2', get(foo, bar_pmtu))

bar_subnet = f'{bar.name}.Subnet'
for i in range(1, 4):
    sub = f'{i}.{i}.{i}.{i}'
    foo.cmd('add', bar_subnet, sub)
    foo.cmd('add', bar_subnet, sub)

check.equals(['1.1.1.1', '2.2.2.2', '3.3.3.3'],
             get(foo, bar_subnet).splitlines())

foo.cmd('del', bar_subnet, '2.2.2.2')
check.equals(['1.1.1.1', '3.3.3.3'],
             get(foo, bar_subnet).splitlines())

foo.cmd('del', bar_subnet)
subnet, _ = foo.cmd('get', bar_subnet, code=1)
check.false(subnet)

log.info('we should not be able to get/set for nodes with invalid names')

Path(foo.sub('hosts', 'fake-node')).touch(0o644, exist_ok=True)
foo.cmd('set', 'fake-node.Subnet', '1.1.1.1', code=1)

log.info('we should not be able to set obsolete variables unless forced')

foo.cmd('set', 'PrivateKey', '12345', code=1)
foo.cmd('--force', 'set', 'PrivateKey', '67890')
check.equals('67890', get(foo, 'PrivateKey'))

foo.cmd('del', 'PrivateKey')
key, _ = foo.cmd('get', 'PrivateKey', code=1)
check.false(key)

log.info('we should not be able to set/add malformed Subnets')

for subnet in (
        '1.1.1',
        '1:2:3:4:5:',
        '1:2:3:4:5:::6',
        '1:2:3:4:5:6:7:8:9',
        '256.256.256.256',
        '1:2:3:4:5:6:7:8.123',
        '1:2:3:4:5:6:7:1.2.3.4',
        'a:b:c:d:e:f:g:h',
        '1.1.1.1/0',
        '1.1.1.1/-1',
        '1.1.1.1/33',
        '1::/0',
        '1::/-1',
        '1::/129',
        ':' * 1024,
):
    log.info('testing subnet %s', subnet)
    foo.cmd('add', 'Subnet', subnet, code=1)

subnet, _ = foo.cmd('get', 'Subnet', code=1)
check.false(subnet)
