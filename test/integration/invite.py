#!/usr/bin/env python3

from testlib import Tinc, log, Script, check, util


def run_invite_test(start_before_invite: bool):
    foo, bar = Tinc(), Tinc()

    foo.cmd(stdin=f'''
        init {foo.name}
        set Port {foo.port}
        set Address localhost
        set DeviceType dummy
        set Mode switch
        set Broadcast no
    ''')

    foo.add_script(Script.TINC_UP)

    if start_before_invite:
        foo.cmd('start')
        foo[Script.TINC_UP].wait()

    log.info('create invitation')
    foo_invite, _ = foo.cmd('invite', bar.name)
    assert foo_invite

    foo_invite = foo_invite.strip()
    log.info('using invitation %s', foo_invite)

    if not start_before_invite:
        foo.cmd('start')
        foo[Script.TINC_UP].wait()

    log.info('join second node')
    bar.cmd('join', foo_invite)

    log.info('compare configs')
    check.files_eq(foo.sub('hosts', foo.name), bar.sub('hosts', foo.name))

    log.info('compare keys')

    prefix = 'Ed25519PublicKey'
    foo_key = util.find_line(foo.sub('hosts', bar.name), prefix)
    bar_key = util.find_line(bar.sub('hosts', bar.name), prefix)
    check.equals(foo_key, bar_key)

    log.info('checking Mode')
    bar_mode, _ = bar.cmd('get', 'Mode')
    check.equals('switch', bar_mode.strip())

    log.info('checking Broadcast')
    bar_bcast, _ = bar.cmd('get', 'Broadcast')
    check.equals('no', bar_bcast.strip())

    log.info('checking ConnectTo')
    bar_conn, _ = bar.cmd('get', 'ConnectTo')
    check.equals(foo.name, bar_conn.strip())

    log.info('configuring %s', bar.name)
    bar.cmd(stdin='''
        set DeviceType dummy
        set Port 0
    ''')

    log.info('adding scripts')
    foo.add_script(bar.script_up)
    bar.add_script(foo.script_up)

    log.info('starting %s', bar.name)
    bar.cmd('start')

    log.info('waiting for nodes to come up')
    foo[bar.script_up].wait()
    bar[foo.script_up].wait()

    log.info('checking required nodes')
    check.nodes(foo, 2)
    check.nodes(bar, 2)

    foo.cmd('stop')
    bar.cmd('stop')


log.info('testing in offline mode')
run_invite_test(start_before_invite=False)

log.info('testing in online mode')
run_invite_test(start_before_invite=True)
