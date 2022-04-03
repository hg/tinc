#!/usr/bin/env python3

from testlib import Script, Tinc, log, check, Test


def init(t: Test) -> Tinc:
    node = t.node()
    node.add_script(Script.TINC_UP)
    node.cmd(
        stdin=f"""
        init {node.name}
        set DeviceType dummy
        set Port 0
    """
    )
    return node


def test(t: Test, *flags: str) -> None:
    log.info("init new node")
    node = init(t)

    log.info('starting tincd with flags "%s"', " ".join(flags))
    tincd = node.tincd(*flags)

    log.info("waiting for tinc-up script")
    node[Script.TINC_UP].wait()

    log.info("stopping tincd")
    node.cmd("stop")

    log.info("checking tincd exit code")
    check.equals(0, tincd.wait())


with Test("foreground mode") as t:
    test(t, "-D")

with Test("background mode") as t:
    test(t)
