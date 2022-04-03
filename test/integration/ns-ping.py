#!/usr/bin/env python3

import subprocess as subp
import typing as T

from testlib import Script, Tinc, log, cmd, util, ext, Test
from testlib.template import make_netns_config

util.require_root()
util.require_command("ip", "netns", "list")
util.require_path("/dev/net/tun")

ip_foo = "192.168.1.1"
ip_bar = "192.168.1.2"
mask = 24


def init(t: Test) -> T.Tuple[Tinc, Tinc]:
    foo, bar = t.node(), t.node()

    log.info("create network namespaces")
    ext.netns_add(foo.name)
    ext.netns_add(bar.name)

    log.info("initialize two nodes")

    stdin = f"""
        init {foo.name}
        set Port {foo.port}
        set Subnet {ip_foo}
        set Interface {foo.name}
        set Address localhost
        set AutoConnect no
    """
    foo.cmd(stdin=stdin)

    stdin = f"""
        init {bar.name}
        set Port {bar.port}
        set Subnet {ip_bar}
        set Interface {bar.name}
        set AutoConnect no
    """
    bar.cmd(stdin=stdin)

    foo.add_script(Script.TINC_UP, make_netns_config(foo.name, ip_foo, mask))
    bar.add_script(Script.TINC_UP, make_netns_config(bar.name, ip_bar, mask))

    log.info("exchange configuration files")
    cmd.exchange(foo, bar)

    return foo, bar


def ping(ns: str, ip: str) -> int:
    log.info("pinging node from netns %s at %s", ns, ip)
    proc = subp.run(["ip", "netns", "exec", ns, "ping", "-W1", "-c1", ip])
    return proc.returncode


with Test("ns-ping") as t:
    foo, bar = init(t)
    foo.cmd("start")
    bar.cmd("start")

    log.info("waiting for nodes to come up")
    foo[Script.TINC_UP].wait()
    bar[Script.TINC_UP].wait()

    log.info("ping must not work when there is no connection")
    assert ping(foo.name, ip_bar)

    log.info("add script foo/host-up")
    bar.add_script(foo.script_up)

    log.info("add ConnectTo clause")
    bar.cmd("add", "ConnectTo", foo.name)

    log.info("bar waits for foo")
    bar[foo.script_up].wait()

    log.info("ping must work after connection is up")
    assert not ping(foo.name, ip_bar)
