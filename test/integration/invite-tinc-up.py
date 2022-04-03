#!/usr/bin/env python3

import os
import typing as T

from testlib import Test, Tinc, Script, log, util, check

ifconfig = "93.184.216.34/24"
route_v6 = ("2606:2800:220:1::/64", "2606:2800:220:1:248:1893:25c8:1946")
bad_ipv4 = "1234::"
ed_pubkey = "Ed25519PublicKey"


def make_inv_created(export: str) -> str:
    return f'''
    node, invite = os.environ['NODE'], os.environ['INVITATION_FILE']
    log.info('writing to invitation file %s, node %s', invite, node)

    script = f"""
Name = {{node}}
Ifconfig = {ifconfig}
Route = {' '.join(route_v6)}
Route = 1.2.3.4 {bad_ipv4}

{export}
""".strip()

    with open(invite, 'w') as f:
        f.write(script)
    '''


def init(t: Test) -> T.Tuple[Tinc, Tinc]:
    foo, bar = t.node(), t.node()

    foo.cmd(
        stdin=f"""
        init {foo.name}
        set DeviceType dummy
        set Address localhost
        set Port {foo.port}
    """
    )

    log.info("start node %s", foo)
    foo.add_script(Script.TINC_UP)
    foo.cmd("start")
    foo[Script.TINC_UP].wait()

    return foo, bar


with Test("invite-tinc-up") as t:
    foo, bar = init(t)

    log.info("run export")
    export, _ = foo.cmd("export")
    assert export

    log.info("adding invitation-created script")
    code = make_inv_created(export)
    foo.add_script(Script.INVITATION_CREATED, code)

    log.info("inviting %s", bar)
    url, _ = foo.cmd("invite", bar.name)
    url = url.strip()
    assert url

    log.info('joining %s to %s with "%s"', bar, foo, url)
    bar.cmd("--batch", "join", url)

    log.info("comparing host configs")
    check.files_eq(foo.sub("hosts", foo.name), bar.sub("hosts", foo.name))

    log.info("comparing public keys")
    foo_key = util.find_line(foo.sub("hosts", bar.name), ed_pubkey)
    bar_key = util.find_line(bar.sub("hosts", bar.name), ed_pubkey)
    check.equals(foo_key, bar_key)

    log.info("bar.tinc-up must not exist")
    assert not os.path.exists(bar.sub("tinc-up"))

    inv = bar.sub("tinc-up.invitation")
    log.info("testing %s", inv)

    content = util.read_text(inv)
    check.in_(ifconfig, content)
    check.not_in(bad_ipv4, content)

    for v6 in route_v6:
        check.in_(v6, content)

    if os.name != "nt":
        assert not os.access(inv, os.X_OK)
