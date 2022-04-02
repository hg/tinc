#!/usr/bin/env python3

import subprocess as subp
import typing as T

from testlib import Script, Tinc, log, path, check, cmd

tarpit_timeout = 2


def init(*options: str) -> T.Tuple[Tinc, Tinc]:
    custom = '\n'.join(options)
    log.info('initialize two nodes with options "%s"', custom)

    foo, bar = Tinc(), Tinc()

    foo.cmd(stdin=f'''
        init {foo}
        set DeviceType dummy
        set Port {foo.port}
        set Address localhost
        set AutoConnect no
        set Subnet 10.96.96.1
        {custom}
    ''')

    bar.cmd(stdin=f'''
        init {bar}
        set DeviceType dummy
        set Port {bar.port}
        set AutoConnect no
        set Subnet 10.96.96.2
        {custom}
    ''')

    log.info('exchange host configs')

    cmd.exchange(foo, bar)

    foo.add_script(Script.SUBNET_UP)
    bar.add_script(Script.SUBNET_UP)

    return foo, bar


def splice(foo: Tinc, bar: Tinc, protocol: str) -> subp.Popen:
    return subp.Popen([path.splice_path,
                       foo.name, 'localhost', str(foo.port),
                       bar.name, 'localhost', str(bar.port),
                       protocol])


def test_splice(foo: Tinc, bar: Tinc, protocol: str) -> None:
    log.info('no splicing allowed, protocol %s', protocol)

    foo.cmd('start')
    bar.cmd('start')

    foo[Script.SUBNET_UP].wait()
    bar[Script.SUBNET_UP].wait()

    sp = splice(foo, bar, '17.7')
    try:
        check.nodes(foo, 1)
        check.nodes(bar, 1)
    finally:
        sp.kill()

    bar.cmd('stop')
    foo.cmd('stop')


foo, bar = init()
test_splice(foo, bar, '17.7')

foo, bar = init('set ExperimentalProtocol no')
test_splice(foo, bar, '17.0')
