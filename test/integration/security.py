#!/usr/bin/env python3

import subprocess as subp
import socket
import time

from testlib import Script, Tinc, log, path, check, cmd

foo, bar = Tinc(), Tinc()


def splice(protocol: str) -> subp.Popen:
    return subp.Popen([path.splice_path,
                       foo.name, 'localhost', str(foo.port),
                       bar.name, 'localhost', str(bar.port),
                       protocol])


def send(buf: str, delay: int = 0) -> bytes:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.connect(('localhost', foo.port))

        if delay:
            time.sleep(delay)

        received = b''
        try:
            sock.sendall(bytes(f'{buf}\n', 'utf-8'))
            sock.settimeout(1)
            while True:
                rec = sock.recv(4096)
                assert rec
                received += rec
        except socket.timeout:
            log.info('received: "%s"', received)
            return received


log.info('initialize two nodes')

tarpit_timeout = 2

foo.cmd(stdin=f'''
    init {foo}
    set DeviceType dummy
    set Port {foo.port}
    set Address localhost
    set PingTimeout {tarpit_timeout}
    set AutoConnect no
    set Subnet 10.96.96.1
''')

bar.cmd(stdin=f'''
    init {bar}
    set DeviceType dummy
    set Port {bar.port}
    set PingTimeout {tarpit_timeout}
    set MaxTimeout {tarpit_timeout}
    set ExperimentalProtocol no
    set AutoConnect no
    set Subnet 10.96.96.2
''')

log.info('exchange host configs')

cmd.exchange(foo, bar)

foo.add_script(Script.SUBNET_UP)
bar.add_script(Script.SUBNET_UP)

foo.cmd('start')
bar.cmd('start')

foo[Script.SUBNET_UP].wait()
bar[Script.SUBNET_UP].wait()

id_bar = f'0 {bar} 17.7'
id_foo = f'0 {foo} 17.7'
id_baz = '0 baz 17.7'

log.info('no ID sent by responding node if we do not send an ID first before the timeout')
assert not send(id_bar, delay=tarpit_timeout * 2)

log.info('ID sent if initiator sends first, but still tarpitted')
assert send(id_bar).startswith(bytes(id_foo, 'utf-8'))

log.info('no invalid IDs allowed')
assert not send(id_foo)
assert not send(id_baz)

null_metakey = f'''
0 {foo} 17.0\
1 0 672 0 0 834188619F4D943FD0F4B1336F428BD4AC06171FEABA66BD2356BC9593F0ECD643F\
0E4B748C670D7750DFDE75DC9F1D8F65AB1026F5ED2A176466FBA4167CC567A2085ABD070C1545B\
180BDA86020E275EA9335F509C57786F4ED2378EFFF331869B856DDE1C05C461E4EECAF0E2FB97A\
F77B7BC2AD1B34C12992E45F5D1254BBF0C3FB224ABB3E8859594A83B6CA393ED81ECAC9221CE6B\
C71A727BCAD87DD80FC0834B87BADB5CB8FD3F08BEF90115A8DF1923D7CD9529729F27E1B8ABD83\
C4CF8818AE10257162E0057A658E265610B71F9BA4B365A20C70578FAC65B51B91100392171BA12\
A440A5E93C4AA62E0C9B6FC9B68F953514AAA7831B4B2C31C4
'''.strip()

log.info('no NULL METAKEY allowed')
assert not send(null_metakey)

log.info('no splicing allowed')

bar.cmd('stop')
bar.cmd('del', 'ExperimentalProtocol')

bar.add_script(Script.SUBNET_UP)
bar.cmd('start')
bar[Script.SUBNET_UP].wait()

sp = splice('17.7')
try:
    check.nodes(foo, 1)
    check.nodes(bar, 1)
finally:
    sp.kill()

bar.cmd('stop')
foo.cmd('stop')

log.info('test splicing with legacy protocol')

foo.cmd('set', 'ExperimentalProtocol', 'no')
bar.cmd('set', 'ExperimentalProtocol', 'no')

foo.add_script(Script.SUBNET_UP)
foo.cmd('start')
foo[Script.SUBNET_UP].wait()

bar.add_script(Script.SUBNET_UP)
bar.cmd('start')
bar[Script.SUBNET_UP].wait()

sp = splice('17.0')
try:
    check.nodes(foo, 1)
    check.nodes(bar, 1)
finally:
    sp.kill()
