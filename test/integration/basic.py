#!/usr/bin/env python3

from testlib import Script, Tinc

foo = Tinc()

foo.add_script(Script.TINC_UP)

foo.cmd(stdin=f'''
    init {foo.name}
    set DeviceType dummy
    set Port 0
''')


def test(*flags: str):
    tincd = foo.tincd(*flags)
    foo[Script.TINC_UP].wait()
    foo.cmd('stop')
    assert not tincd.wait()


test('-D')
test()
