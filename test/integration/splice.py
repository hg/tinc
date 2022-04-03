#!/usr/bin/env python3

import os
import subprocess as subp
import typing as T

from testlib import Script, Tinc, log, path, check, cmd


def init(*options: str) -> T.Tuple[Tinc, Tinc]:
    custom = os.linesep.join(options)
    log.info('init two nodes with options "%s"', custom)

    foo, bar = Tinc(), Tinc()

    foo.cmd(
        stdin=f"""
        init {foo}
        set DeviceType dummy
        set Port {foo.port}
        set Address localhost
        set AutoConnect no
        set Subnet 10.96.96.1
        {custom}
    """
    )

    bar.cmd(
        stdin=f"""
        init {bar}
        set DeviceType dummy
        set Port {bar.port}
        set AutoConnect no
        set Subnet 10.96.96.2
        {custom}
    """
    )

    log.info("exchange host configs")

    cmd.exchange(foo, bar)

    foo.add_script(Script.SUBNET_UP)
    bar.add_script(Script.SUBNET_UP)

    return foo, bar


def splice(foo: Tinc, bar: Tinc, protocol: str) -> subp.Popen:
    args = [
        path.splice_path,
        foo.name,
        "localhost",
        str(foo.port),
        bar.name,
        "localhost",
        str(bar.port),
        protocol,
    ]
    log.info("starting splice with args %s", args)
    return subp.Popen(args)


def test_splice(protocol: str, *options: str) -> None:
    log.info("no splicing allowed (%s)", protocol)

    foo, bar = init(*options)

    foo.cmd("start")
    bar.cmd("start")

    log.info("waiting for subnets to come up")
    foo[Script.SUBNET_UP].wait()
    bar[Script.SUBNET_UP].wait()

    sp = splice(foo, bar, protocol)
    try:
        check.nodes(foo, 1)
        check.nodes(bar, 1)
    finally:
        sp.kill()

    log.info("stopping nodes")
    bar.cmd("stop")
    foo.cmd("stop")


test_splice("17.7")
test_splice("17.0", "set ExperimentalProtocol no")
