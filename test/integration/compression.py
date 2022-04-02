#!/usr/bin/env python3

import sys
import os
import multiprocessing.connection as mpc
import time

from testlib import cmd, check

content = "zHgfHEzRsKPU41rWoTzmcxxxUGvjfOtTZ0ZT2S1GezL7QbAcMGiLa8i6JOgn59Dq5BtlfbZj"


def do_server():
    port = int(os.environ['PORT'])
    with mpc.Listener((os.environ['ADDR'], port)) as listener:
        with listener.accept() as conn:
            data = conn.recv()
            print(data, sep='')
    sys.exit(0)


def do_client():
    port = int(os.environ['PORT'])
    for retry in range(5):
        try:
            with mpc.Client((os.environ['ADDR'], port)) as client:
                client.send(content)
            break
        except ConnectionRefusedError:
            time.sleep(1)
    sys.exit(0)


def main():
    import atexit
    import subprocess as subp
    from testlib import Script, Tinc, log
    from testlib.path import python_path
    from testlib.util import require_root, require_command, require_path, random_port

    require_root()
    require_command('ip', 'netns', 'list')
    require_path('/dev/net/tun')

    ip_foo = '192.168.1.1'
    ip_bar = '192.168.1.2'

    def make_tinc_up(tinc: Tinc, ip: str) -> str:
        return f'''
    iface = os.environ['INTERFACE']
    log.info('using interface', iface)
    subp.run(['ip', 'link', 'set', 'dev', iface, 'netns', '{tinc.name}'], check=True)
    subp.run(['ip', 'netns', 'exec', '{tinc.name}', 'ip', 'addr', 'add', '{ip}/{24}', 'dev', iface], check=True)
    subp.run(['ip', 'netns', 'exec', '{tinc.name}', 'ip', 'link', 'set', iface, 'up'], check=True)
'''

    log.info('determining supported compression levels')

    foo, bar = Tinc(), Tinc()

    version, _ = foo.tincd('--version').communicate()
    assert version

    levels: [int] = []
    bogus_levels: [int] = []

    for algo, (fr, to) in (
            ('zlib', (1, 9)),
            ('lzo', (10, 11)),
            ('lz4', (12, 12)),
    ):
        lvls = range(fr, to + 1)
        if f'comp_{algo}' in version:
            levels += lvls
        else:
            bogus_levels += lvls

    log.info('supported compression levels: %s', ' '.join(map(str, levels)))
    log.info('unsupported compression levels: %s', ' '.join(map(str, bogus_levels)))

    log.info('create network namespaces')

    def ns_action(action: str) -> None:
        subp.run(['ip', 'netns', action, foo.name], check=True)
        subp.run(['ip', 'netns', action, bar.name], check=True)

    ns_action('add')
    atexit.register(lambda: ns_action('delete'))

    log.info('initialize two nodes')

    foo.cmd(stdin=f'''
        init {foo.name}
        set Port {foo.port}
        set Subnet {ip_foo}
        set Interface {foo.name}
        set Address localhost
    ''')

    bar.cmd(stdin=f'''
        init {bar.name}
        set Subnet {ip_bar}
        set Interface {bar.name}
        set ConnectTo {foo.name}
    ''')

    foo.add_script(Script.TINC_UP, make_tinc_up(foo, ip_foo))
    bar.add_script(Script.TINC_UP, make_tinc_up(bar, ip_bar))

    log.info('exchange configuration files')

    cmd.exchange(foo, bar)

    foo.add_script(bar.script_up)
    bar.add_script(foo.script_up)

    port = random_port()

    for level in levels:
        log.info('testing compression level %d', level)

        foo.cmd('set', 'Compression', str(level))
        bar.cmd('set', 'Compression', str(level))

        foo.cmd('start')
        bar.cmd('start')

        foo[Script.TINC_UP].wait()
        bar[Script.TINC_UP].wait()

        foo[bar.script_up].wait()
        bar[foo.script_up].wait()

        env = {'ADDR': ip_foo, 'PORT': str(port)}

        log.info('start receiver in network namespace %s', foo.name)

        receiver = subp.Popen(['ip', 'netns', 'exec', foo.name, python_path, __file__, '-s'],
                              env=env,
                              stdout=subp.PIPE,
                              encoding='utf-8')

        log.info('start sender in network namespace %s', bar.name)

        sender = subp.Popen(['ip', 'netns', 'exec', bar.name, python_path, __file__, '-c'], env=env)

        recv, _ = receiver.communicate()
        log.info('received %d bytes', len(recv))

        check.equals(0, sender.wait())
        check.equals(content, recv.rstrip())

        foo.cmd('stop')
        bar.cmd('stop')

    log.info('invalid compression levels should fail')

    for level in bogus_levels:
        log.info('testing bogus compression level %d', level)

        foo.cmd('set', 'Compression', str(level))

        tincd = foo.tincd()
        _, stderr = tincd.communicate()

        check.equals(1, tincd.returncode)
        check.in_('Bogus compression level', stderr)


last = sys.argv[-1]

if last == '-s':
    do_server()
elif last == '-c':
    do_client()
else:
    main()
