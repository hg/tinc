#!/usr/bin/env python3

import os.path
import typing as T

from testlib import Script, Tinc, log, check, Test
from testlib.util import random_string

subnet_foo = ("10.0.0.1", "fec0::/64")
subnet_bar = ("10.0.0.2", "fec0::/64#5")
netnames = (random_string(10), random_string(10), random_string(10))


def init(t: Test) -> T.Tuple[Tinc, Tinc]:
    foo, bar = t.node(), t.node()

    stdin = f"""
        init {foo.name}
        set DeviceType dummy
        set Port {foo.port}
        set Address 127.0.0.1
        add Subnet {subnet_foo[0]}
        add Subnet {subnet_foo[1]}
    """
    foo.cmd(stdin=stdin)

    for script in (
        Script.TINC_UP,
        Script.TINC_DOWN,
        Script.HOST_UP,
        Script.HOST_DOWN,
        Script.SUBNET_UP,
        Script.SUBNET_DOWN,
        foo.script_up,
        foo.script_down,
        bar.script_up,
        bar.script_down,
        Script.INVITATION_CREATED,
        Script.INVITATION_ACCEPTED,
    ):
        foo.add_script(script)

    return foo, bar


def wait_tinc(foo: Tinc, script: Script) -> None:
    log.info("checking tinc: %s %s", foo, script)

    env = foo[script].wait().env
    check.equals(netnames[0], env["NETNAME"])
    check.equals(foo.name, env["NAME"])
    check.equals("dummy", env["DEVICE"])


def wait_subnet(foo: Tinc, script: Script, node: Tinc, subnet: str) -> None:
    log.info("checking subnet: %s %s %s %s", foo, script, node, subnet)

    env = foo[script].wait().env
    check.equals(netnames[0], env["NETNAME"])
    check.equals(foo.name, env["NAME"])
    check.equals("dummy", env["DEVICE"])
    check.equals(node.name, env["NODE"])

    if node != foo:
        check.equals("127.0.0.1", env["REMOTEADDRESS"])
        check.equals(str(node.port), env["REMOTEPORT"])

    if "#" in subnet:
        addr, weight = subnet.split("#")
        check.equals(addr, env["SUBNET"])
        check.equals(weight, env["WEIGHT"])
    else:
        check.equals(subnet, env["SUBNET"])


def wait_host(foo: Tinc, bar: Tinc, script: T.Union[Script, str]) -> None:
    log.info("checking host: %s %s %s", foo, bar, script)

    env = foo[script].wait().env
    check.equals(netnames[0], env["NETNAME"])
    check.equals(foo.name, env["NAME"])
    check.equals("dummy", env["DEVICE"])
    check.equals(bar.name, env["NODE"])
    check.equals("127.0.0.1", env["REMOTEADDRESS"])
    check.equals(str(bar.port), env["REMOTEPORT"])


def test_start_server(foo: Tinc) -> None:
    foo.cmd("-n", netnames[0], "start")
    wait_tinc(foo, Script.TINC_UP)

    log.info("test server subnet-up")
    for sub in subnet_foo:
        wait_subnet(foo, Script.SUBNET_UP, foo, sub)


def test_invite_client(foo: Tinc, bar: Tinc) -> str:
    url, _ = foo.cmd("-n", netnames[1], "invite", bar.name)
    url = url.strip()
    check.true(url)

    env = foo[Script.INVITATION_CREATED].wait().env
    check.equals(netnames[1], env["NETNAME"])
    check.equals(foo.name, env["NAME"])
    check.equals(bar.name, env["NODE"])
    check.equals(url, env["INVITATION_URL"])
    assert os.path.isfile(env["INVITATION_FILE"])

    return url


def test_join_client(foo: Tinc, bar: Tinc, url: str) -> None:
    bar.cmd("-n", netnames[2], "join", url)

    env = foo[Script.INVITATION_ACCEPTED].wait().env
    check.equals(netnames[0], env["NETNAME"])
    check.equals(foo.name, env["NAME"])
    check.equals("dummy", env["DEVICE"])
    check.equals(bar.name, env["NODE"])
    check.equals("127.0.0.1", env["REMOTEADDRESS"])


def test_start_client(foo: Tinc, bar: Tinc) -> None:
    stdin = f"""
        set DeviceType dummy
        set Port {bar.port}
        add Subnet {subnet_bar[0]}
        add Subnet {subnet_bar[1]}
    """
    bar.cmd(stdin=stdin)

    log.info("start client")
    bar.cmd("start")
    wait_host(foo, bar, Script.HOST_UP)
    wait_host(foo, bar, bar.script_up)

    log.info("test client subnet-up")
    for sub in subnet_bar:
        wait_subnet(foo, Script.SUBNET_UP, bar, sub)


def test_stop_client(foo: Tinc, bar: Tinc) -> None:
    bar.cmd("stop")
    wait_host(foo, bar, Script.HOST_DOWN)
    wait_host(foo, bar, bar.script_down)

    log.info("testing client subnet-down")
    for sub in subnet_bar:
        wait_subnet(foo, Script.SUBNET_DOWN, bar, sub)


def test_stop_server(foo: Tinc, bar: Tinc) -> None:
    log.info("start client")
    bar.cmd("start")
    wait_host(foo, bar, bar.script_up)

    log.info("stop server")
    foo.cmd("stop")
    wait_host(foo, bar, Script.HOST_DOWN)
    wait_host(foo, bar, bar.script_down)

    log.info("test client subnet-down")
    for sub in subnet_bar:
        wait_subnet(foo, Script.SUBNET_DOWN, bar, sub)

    log.info("test server subnet-down")
    for sub in subnet_foo:
        wait_subnet(foo, Script.SUBNET_DOWN, foo, sub)

    log.info("test tinc-down")
    wait_tinc(foo, Script.TINC_DOWN)


with Test("scripts test") as t:
    foo, bar = init(t)

    log.info("start server")
    test_start_server(foo)

    log.info("invite client")
    url = test_invite_client(foo, bar)

    log.info('join client via url "%s"', url)
    test_join_client(foo, bar, url)

    log.info("start client")
    test_start_client(foo, bar)

    log.info("stop client")
    test_stop_client(foo, bar)

    log.info("stop server")
    test_stop_server(foo, bar)
