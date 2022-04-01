#!/usr/bin/env python3

from testlib import Script, Tinc, log, cmd, util
import atexit
import subprocess as subp

util.require_root()
util.require_command('ip', 'netns', 'list')
util.require_path('/dev/net/tun')

ns1, ns2 = 'ping.test1', 'ping.test2'


def ns_manage(cmd: str) -> None:
    for ns in (ns1, ns2):
        subp.run(['ip', 'netns', cmd, ns], check=True)


log.info('create network namespaces')
ns_manage('add')
atexit.register(lambda: ns_manage('delete'))

log.info('initialize two nodes')

ip_foo = '192.168.1.1'
ip_bar = '192.168.1.2'
mask = '24'

foo, bar = Tinc(), Tinc()

foo.cmd(stdin=f'''
    init {foo.name}
    set Port {foo.port}
    set Subnet {ip_foo}
    set Interface {ns1}
    set Address localhost
    set AutoConnect no
''')

bar.cmd(stdin=f'''
    init {bar.name}
    set Port {bar.port}
    set Subnet {ip_bar}
    set Interface {ns2}
    set AutoConnect no
''')


def make_tinc_up(ns: str, ip: str) -> str:
    return f'''
    iface = os.environ['INTERFACE']
    subp.run(['ip', 'link', 'set', 'dev', iface, 'netns', '{ns}'], check=True)
    subp.run(['ip', 'netns', 'exec', '{ns}', 'ip', 'addr', 'add', '{ip}/{mask}', 'dev', iface], check=True)
    subp.run(['ip', 'netns', 'exec', '{ns}', 'ip', 'link', 'set', iface, 'up'], check=True)
    '''


foo.add_script(Script.TINC_UP, make_tinc_up(ns1, ip_foo))
bar.add_script(Script.TINC_UP, make_tinc_up(ns2, ip_bar))

log.info('exchange configuration files')

cmd.exchange(foo, bar)

log.info('start tinc')

foo.cmd('start')
bar.cmd('start')

foo[Script.TINC_UP].wait()
bar[Script.TINC_UP].wait()


def ping_ok() -> bool:
    result = subp.run(['ip', 'netns', 'exec', ns1, 'ping', '-W1', '-c3', ip_bar])
    return result == 0


log.info('nodes should not be able to ping each other if there is no connection')

assert not ping_ok()

log.info('after connecting they should be')

bar.add_script(foo.script_up)

bar.cmd('add', 'ConnectTo', foo.name)
bar[foo.script_up].wait()

assert ping_ok()

foo.cmd('stop')
bar.cmd('stop')
