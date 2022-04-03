#!/usr/bin/env python3

import sys
import os
import multiprocessing.connection as mpc
import time
import typing as T

ip_foo = "192.168.1.1"
ip_bar = "192.168.1.2"
mask = 24

content = "zHgfHEzRsKPU41rWoTzmcxxxUGvjfOtTZ0ZT2S1GezL7QbAcMGiLa8i6JOgn59Dq5BtlfbZj"


def run_server(addr: str, port: int) -> None:
    with mpc.Listener((addr, port)) as listener:
        with listener.accept() as conn:
            data = conn.recv()
            print(data, sep="")
    sys.exit(0)


def run_client(addr: str, port: int) -> None:
    for retry in range(5):
        try:
            with mpc.Client((addr, port)) as client:
                client.send(content)
            break
        except ConnectionRefusedError:
            time.sleep(1)


def get_compression_levels(features) -> T.Tuple[T.List[int], T.List[int]]:
    from testlib import log, Feature

    log.info("getting supported compression levels")

    levels: T.List[int] = []
    bogus: T.List[int] = []

    for comp, (fr, to) in (
        (Feature.COMP_ZLIB, (1, 9)),
        (Feature.COMP_LZO, (10, 11)),
        (Feature.COMP_LZ4, (12, 12)),
    ):
        lvls = range(fr, to + 1)
        if comp in features:
            levels += lvls
        else:
            bogus += lvls

    log.info("supported compression levels: %s", levels)
    log.info("unsupported compression levels: %s", bogus)

    return levels, bogus


def init(t):
    from testlib import Script, log, cmd, Tinc, ext
    from testlib.template import make_netns_config

    foo: Tinc = t.node()
    foo.cmd(
        stdin=f"""
        init {foo.name}
        set Port {foo.port}
        set Subnet {ip_foo}
        set Interface {foo.name}
        set Address localhost
    """
    )
    ext.netns_add(foo.name)
    foo.add_script(Script.TINC_UP, make_netns_config(foo.name, ip_foo, mask))

    bar: Tinc = t.node()
    bar.cmd(
        stdin=f"""
        init {bar.name}
        set Subnet {ip_bar}
        set Interface {bar.name}
        set ConnectTo {foo.name}
    """
    )
    ext.netns_add(bar.name)
    bar.add_script(Script.TINC_UP, make_netns_config(bar.name, ip_bar, mask))

    log.info("exchange configuration files")
    cmd.exchange(foo, bar)

    foo.add_script(bar.script_up)
    bar.add_script(foo.script_up)

    return foo, bar


def test_valid_level(foo, bar, level: int, env: T.Dict[str, str]):
    import subprocess as subp
    from testlib import log, path, check

    foo.cmd("set", "Compression", str(level))
    bar.cmd("set", "Compression", str(level))

    foo.cmd("start")
    bar.cmd("start")

    foo[bar.script_up].wait()
    bar[foo.script_up].wait()

    log.info("start receiver in netns")
    receiver = subp.Popen(
        ["ip", "netns", "exec", foo.name, path.python_path, __file__, "--recv"],
        env=env,
        stdout=subp.PIPE,
        encoding="utf-8",
    )

    log.info("start sender in netns")
    sender = subp.Popen(
        ["ip", "netns", "exec", bar.name, path.python_path, __file__, "--send"],
        env=env,
        stderr=subp.PIPE,
    )

    recv, _ = receiver.communicate()
    log.info("received %d bytes", len(recv))

    out, err = sender.communicate()
    log.info('sender printed ("%s", "%s")', out, err)

    check.equals(0, sender.returncode)
    check.equals(content, recv.rstrip())

    foo.cmd("stop")
    bar.cmd("stop")


def test_bogus_level(node, level: int):
    from testlib import log, check

    log.info(f"fail on invalid level {level}")
    node.cmd("set", "Compression", str(level))
    tincd = node.tincd()
    _, stderr = tincd.communicate()
    check.equals(1, tincd.returncode)
    check.in_("Bogus compression level", stderr)


def run_tests():
    from testlib import Test
    from testlib.util import random_port

    env = {"ADDR": ip_foo, "PORT": str(random_port())}

    with Test("compression support") as t:
        foo, bar = init(t)
        levels, bogus = get_compression_levels(foo.features)

        for level in levels:
            test_valid_level(foo, bar, level, env)

        for level in bogus:
            test_bogus_level(foo, level)


last = sys.argv[-1]
addr = os.environ.get("ADDR", "")
port = int(os.environ.get("PORT", "-1"))

if last == "--recv":
    run_server(addr, port)
elif last == "--send":
    run_client(addr, port)
else:
    from testlib import util

    util.require_root()
    util.require_command("ip", "netns", "list")
    util.require_path("/dev/net/tun")
    run_tests()
