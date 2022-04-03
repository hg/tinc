#!/usr/bin/env python3

import typing as T

from testlib import Tinc, log, cmd, check, Test


def init(t: Test) -> T.Tuple[Tinc, Tinc]:
    foo, bar = t.node(), t.node()

    stdin = f"""
        init {foo.name}
        set Port {foo.port}
        set DeviceType dummy
        set Address localhost
        set ExperimentalProtocol no
    """
    foo.cmd(stdin=stdin)

    stdin = f"""
        init {bar.name}
        set Port 0
        set DeviceType dummy
        set ExperimentalProtocol no
    """
    bar.cmd(stdin=stdin)

    foo.add_script(bar.script_up)
    bar.add_script(foo.script_up)

    cmd.exchange(foo, bar)
    bar.cmd("add", "ConnectTo", foo.name)

    return foo, bar


def test(foo: Tinc, bar: Tinc) -> None:
    foo.cmd("start")
    bar.cmd("start")

    log.info("waiting for bar to come up")
    foo[bar.script_up].wait()

    log.info("waiting for foo to come up")
    bar[foo.script_up].wait()

    log.info("checking node reachability")
    stdout, _ = foo.cmd("info", bar.name)
    check.in_("reachable", stdout)

    foo.cmd("stop")
    bar.cmd("stop")


with Test("compression") as t:
    foo, bar = init(t)

    for digest in ("none", "sha256", "sha512"):
        foo.cmd("set", "Digest", digest)

        for cipher in ("none", "aes-256-cbc"):
            foo.cmd("set", "Cipher", cipher)
            test(foo, bar)
