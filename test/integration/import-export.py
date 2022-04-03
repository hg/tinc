#!/usr/bin/env python3

import typing as T

from testlib import Tinc, Script, log, cmd, check, Test


def init(t: Test) -> T.Tuple[Tinc, Tinc, Tinc]:
    foo, bar, baz = t.node(), t.node(), t.node()

    log.info("configure %s", foo.name)
    foo.cmd(
        stdin=f"""
        init {foo.name}
        set DeviceType dummy
        set Port {foo.port}
        set Address localhost
    """
    )

    log.info("configure %s", bar.name)
    bar.cmd(
        stdin=f"""
        init {bar.name}
        set DeviceType dummy
        set Port 0
    """
    )

    log.info("configure %s", baz.name)
    baz.cmd(
        stdin=f"""
        init {baz.name}
        set DeviceType dummy
        set Port 0
    """
    )

    return foo, bar, baz


with Test("import-export") as t:
    foo, bar, baz = init(t)

    log.info("run exchange")
    cmd.exchange(foo, bar)

    log.info("run exchange with export-all")
    cmd.exchange(foo, baz, export_all=True)

    log.info("run exchange-all")
    out, err = foo.cmd("exchange-all", code=1)
    check.in_("No host configuration files imported", err)

    log.info("run import")
    bar.cmd("import", stdin=out)

    for a, b in (
        (foo.sub("hosts", foo.name), bar.sub("hosts", foo.name)),
        (foo.sub("hosts", foo.name), baz.sub("hosts", foo.name)),
        (foo.sub("hosts", bar.name), bar.sub("hosts", bar.name)),
        (foo.sub("hosts", bar.name), baz.sub("hosts", bar.name)),
        (foo.sub("hosts", baz.name), bar.sub("hosts", baz.name)),
        (foo.sub("hosts", baz.name), baz.sub("hosts", baz.name)),
    ):
        log.info("comparing configs %s and %s", a, b)
        check.files_eq(a, b)

    log.info("create %s scripts", foo)

    tinc_up = f"""
    bar, baz = Tinc('{bar}'), Tinc('{baz}')
    bar.cmd('add', 'ConnectTo', this.name)
    baz.cmd('add', 'ConnectTo', this.name)
"""
    foo.add_script(Script.TINC_UP, tinc_up)
    foo.add_script(bar.script_up)
    foo.add_script(baz.script_up)

    log.info("start nodes")
    foo.cmd("start")
    bar.cmd("start")
    baz.cmd("start")

    foo[Script.TINC_UP].wait()
    foo[bar.script_up].wait()
    foo[baz.script_up].wait()

    for tinc in (foo, bar, baz):
        check.nodes(tinc, 3)
