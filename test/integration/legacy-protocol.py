#!/usr/bin/env python3

import typing as T

from testlib import Tinc, Test, Script, log, cmd, check

timeout = 2


def init(t: Test) -> T.Tuple[Tinc, Tinc]:
    foo, bar = t.node(), t.node()

    stdin = f"""
        init {foo.name}
        set DeviceType dummy
        set Port {foo.port}
        set Address localhost
        add Subnet 10.98.98.1
        set PingTimeout {timeout}
    """
    foo.cmd(stdin=stdin)

    stdin = f"""
        init {bar.name}
        set DeviceType dummy
        set Port 0
        add Subnet 10.98.98.2
        set PingTimeout {timeout}
        set MaxTimeout {timeout}
    """
    bar.cmd(stdin=stdin)

    cmd.exchange(foo, bar)
    bar.cmd("add", "ConnectTo", foo.name)

    foo.add_script(bar.script_up)
    bar.add_script(foo.script_up)

    return foo, bar


def run_keys_test(foo: Tinc, bar: Tinc, empty: bool) -> None:
    foo.cmd("start")
    bar.cmd("start")

    foo[bar.script_up].wait()
    bar[foo.script_up].wait()

    check.nodes(foo, 2)
    check.nodes(bar, 2)

    foo_bar, _ = foo.cmd("get", f"{bar.name}.Ed25519PublicKey", code=None)
    log.info('got key foo/bar "%s"', foo_bar)

    bar_foo, _ = bar.cmd("get", f"{foo.name}.Ed25519PublicKey", code=None)
    log.info('got key bar/foo "%s"', bar_foo)

    assert not foo_bar == empty
    assert not bar_foo == empty


with Test("foo 1.1, bar 1.1") as t:
    foo, bar = init(t)
    run_keys_test(foo, bar, empty=False)


with Test("foo 1.1, bar 1.0") as t:
    foo, bar = init(t)
    bar.cmd("set", "ExperimentalProtocol", "no")
    foo.cmd("del", f"{bar}.Ed25519PublicKey")
    bar.cmd("del", f"{foo}.Ed25519PublicKey")
    run_keys_test(foo, bar, empty=True)


with Test("bar 1.0 must not be allowed to connect") as t:
    foo, bar = init(t)
    bar.cmd("set", "ExperimentalProtocol", "no")

    foo_up = foo.add_script(Script.SUBNET_UP)
    bar_up = bar.add_script(Script.SUBNET_UP)

    foo.cmd("start")
    bar.cmd("start")

    foo_up.wait()
    bar_up.wait()

    assert not foo[bar.script_up].wait(timeout * 2)
    check.nodes(foo, 1)
    check.nodes(bar, 1)
