#!/usr/bin/env python3

import os

from . import path
from .notification import notifications


def make_script(node: str, script: str, source: str) -> str:
    return f"""#!{path.python_path}

import os
import sys
import multiprocessing.connection as mpc
import typing as T
import time

def on_error(*args):
    try:
        log.error('Uncaught exception', exc_info=args)
    except NameError:
        print('Uncaught exception', args)
    os.kill({os.getpid()}, 15)

sys.excepthook = on_error
 
os.chdir(r'{path.cwd}')
sys.path.append(r'{path.test_src_root}')

from testlib.proc import Tinc
from testlib.event import Notification
from testlib.log import make_logger

this = Tinc('{node}')
log = make_logger(this.name)

def notify_test(args: T.Dict[str, T.Any] = {{}}, error: T.Optional[Exception] = None):
    log.debug(f'sending notification to port %d', {notifications.port})

    evt = Notification()
    evt.test = '{path.test_name}'
    evt.node = '{node}'
    evt.script = '{script}'
    evt.env = dict(os.environ)
    evt.args = args
    evt.error = error

    for retry in range(1, 5):
        try:
            with mpc.Client(('localhost', {notifications.port})) as conn:
                conn.send(evt)
            log.debug(f'sent notification')
            break
        except Exception as e:
            log.error(f'notification failed', exc_info=True)
            time.sleep(1)

try:
    log.debug('running user code')
{source}
    log.debug('user code finished')
except Exception as e:
    log.error('user code failed', exc_info=True)
    notify_test(error=e)
    sys.exit(1)

notify_test()
"""


def make_cmd_wrap(script: str) -> str:
    cmd = "runpython" if "meson.exe" in path.python_path.lower() else ""

    return f"""
@echo off

set TEST_NAME={path.test_name}
set TINC_PATH={path.tinc_path}
set TINCD_PATH={path.tincd_path}
set SPTPS_TEST_PATH={path.sptps_test_path}
set SPTPS_KEYPAIR_PATH={path.sptps_keypair_path}
set SPLICE_PATH={path.splice_path}

"{path.python_path}" {cmd} "{script}"
"""


def make_netns_config(ns: str, ip: str, mask: int) -> str:
    return f"""
    import subprocess as subp

    iface = os.environ['INTERFACE']
    log.info('using interface %s', iface)
    subp.run(['ip', 'link', 'set', 'dev', iface, 'netns', '{ns}'], check=True)
    subp.run(['ip', 'netns', 'exec', '{ns}', 'ip', 'addr', 'add', '{ip}/{mask}', 'dev', iface], check=True)
    subp.run(['ip', 'netns', 'exec', '{ns}', 'ip', 'link', 'set', iface, 'up'], check=True)
"""
