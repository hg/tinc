#!/usr/bin/env python3

from testlib import Script, Tinc, log, check


def init() -> Tinc:
    node = Tinc()
    node.add_script(Script.TINC_UP)
    node.cmd(stdin=f'''
        init {node.name}
        set DeviceType dummy
        set Port 0
    ''')
    return node


def test(*flags: str) -> None:
    log.info('init new node')
    node = init()

    log.info('starting tincd with flags "%s"', ' '.join(flags))
    tincd = node.tincd(*flags)

    log.info('waiting for tinc-up script')
    node[Script.TINC_UP].wait()

    log.info('stopping tincd')
    node.cmd('stop')

    log.info('checking tincd exit code')
    check.equals(0, tincd.wait())


test('-D')
test()
