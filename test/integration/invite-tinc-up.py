#!/usr/bin/env python3

import os
import pathlib

from testlib import Tinc, Script, log, util, check

foo, bar = Tinc(), Tinc()

foo.cmd(stdin=f'''
    init {foo.name}
    set DeviceType dummy
    set Address localhost
    set Port {foo.port}
''')

log.info('add tinc-up script')
foo.add_script(Script.TINC_UP)

log.info('start node')
foo.cmd('start')
foo[Script.TINC_UP].wait()

log.info('run export')
export, _ = foo.cmd('export')
assert export

ifconfig = '93.184.216.34/24'
route_v6 = ('2606:2800:220:1::/64', '2606:2800:220:1:248:1893:25c8:1946')

foo.add_script(Script.INVITATION_CREATED, f'''
    node, invite = os.environ['NODE'], os.environ['INVITATION_FILE']
    log.info('writing to invitation file %s, node %s', invite, node)

    script = f"""
Name = {{node}}
Ifconfig = {ifconfig}
Route = {' '.join(route_v6)}
Route = 1.2.3.4 1234::

{export}
    """.strip()

    with open(invite, 'w') as f:
        f.write(script)
''')

invite, _ = foo.cmd('invite', bar.name)
invite = invite.strip()
assert invite

log.info('joining %s to %s with "%s"', bar.name, foo.name, invite)
bar.cmd('--batch', 'join', invite)

log.info('comparing host configs')
check.files(foo.sub('hosts', foo.name), bar.sub('hosts', foo.name))

log.info('comparing public keys')
prefix = 'Ed25519PublicKey'
foo_key = util.find_line(foo.sub('hosts', bar.name), prefix)
bar_key = util.find_line(bar.sub('hosts', bar.name), prefix)
assert foo_key == bar_key

bar_tinc_up = bar.sub('tinc-up.invitation')
log.info('testing %s', bar_tinc_up)

content = pathlib.Path(bar_tinc_up).read_text()
assert content
assert ifconfig in content
assert '1234::' not in content

for v6 in route_v6:
    assert v6 in content

assert not os.path.exists(bar.sub('tinc-up'))

if os.name != 'nt':
    assert not os.access(bar_tinc_up, os.X_OK)

foo.cmd('stop')
