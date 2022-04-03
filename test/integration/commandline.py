#!/usr/bin/env python3

from testlib import Script, Tinc, log, check, Test, util

tinc_flags = (
    (0, ("get", "name")),
    (0, ("-n", "foo", "get", "name")),
    (0, ("-nfoo", "get", "name")),
    (0, ("--net=foo", "get", "name")),
    (0, ("--net", "foo", "get", "name")),
    (0, ("-c", "conf", "-c", "conf")),
    (0, ("-n", "net", "-n", "net")),
    (0, ("--pidfile=pid", "--pidfile=pid")),
    (1, ("-n", "foo", "get", "somethingreallyunknown")),
    (1, ("--net",)),
    (1, ("--net", "get", "name")),
    (1, ("foo",)),
    (1, ("-c", "conf", "-n", "n/e\\t")),
)

tincd_flags = (
    (0, ("-D",)),
    (0, ("--no-detach",)),
    (0, ("-D", "-d")),
    (0, ("-D", "-d2")),
    (0, ("-D", "-d", "2")),
    (0, ("-D", "-n", "foo")),
    (0, ("-D", "-nfoo")),
    (0, ("-D", "--net=foo")),
    (0, ("-D", "--net", "foo")),
    (0, ("-D", "-c", ".", "-c", ".")),
    (0, ("-D", "-n", "net", "-n", "net")),
    (0, ("-D", "-n", "net", "-o", "FakeOpt=42")),
    (0, ("-D", "--logfile=log", "--logfile=log")),
    (0, ("-D", "--pidfile=pid", "--pidfile=pid")),
    (1, ("foo",)),
    (1, ("--pidfile",)),
    (1, ("--foo",)),
    (1, ("-n", "net", "-o", "Compression=")),
    (1, ("-c", "fakedir", "-n", "n/e\\t")),
)


def init(t: Test) -> Tinc:
    node = t.node()
    stdin = f"""
        init {node.name}
        set DeviceType dummy
        set Port 0
    """
    node.cmd(stdin=stdin)
    node.add_script(Script.TINC_UP)
    return node


with Test("commandline flags") as t:
    node = init(t)

    for code, flags in tincd_flags:
        cookie = util.random_string(10)
        cmd = node.tincd(*flags, env={"COOKIE": cookie})

        if not code:
            log.info("waiting for tincd to come up")
            env = node[Script.TINC_UP].wait().env
            check.equals(cookie, env["COOKIE"])

        log.info("stopping tinc")
        node.cmd("stop", code=code)

        log.info("reading tincd output")
        stdout, stderr = cmd.communicate()

        log.debug('got code %d, ("%s", "%s")', cmd.returncode, stdout, stderr)
        check.equals(code, cmd.returncode)

    for code, flags in tinc_flags:
        node.cmd(*flags, code=code)
