#!/usr/bin/env python3

import os
from enum import Enum

from . import path
from .notification import NotificationServer
from .util import random_port
from .event import Notification

notifications = NotificationServer(random_port())


class Script(Enum):
    TINC_UP = 'tinc-up'
    TINC_DOWN = 'tinc-down'
    HOST_UP = 'host-up'
    HOST_DOWN = 'host-down'
    SUBNET_UP = 'subnet-up'
    SUBNET_DOWN = 'subnet-down'
    INVITATION_CREATED = 'invitation-created'
    INVITATION_ACCEPTED = 'invitation-accepted'


class TincScript:
    _script: str

    def __init__(self, name: str, script: str, path: str):
        self._name = name
        self._script = script
        self._path = path

    @property
    def _disabled_name(self):
        return f'{self._path}.disabled'

    def wait(self) -> Notification:
        return notifications.get(self._name, self._script)

    @property
    def enabled(self) -> bool:
        return os.path.exists(self._path)

    def enable(self) -> None:
        assert not self.enabled
        os.rename(self._disabled_name, self._path)

    def disable(self) -> None:
        assert self.enabled
        os.rename(self._path, self._disabled_name)


def make_script(node: str, script: str, source: str) -> str:
    return f'''#!{path.python_path}

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
    log.info(f'sending notification to port %d', {notifications.port})

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
            log.info(f'sent notification')
            break
        except Exception as e:
            log.error(f'notification failed', exc_info=True)
            time.sleep(1)

try:
    log.info('running user code')
{source}
    log.info('user code finished')
except Exception as e:
    log.error('user code failed', exc_info=True)
    notify_test(error=e)
    sys.exit(1)

notify_test()
'''


def make_cmd_wrap(script: str) -> str:
    cmd = 'runpython' if 'meson.exe' in path.python_path.lower() else ''

    return f'''
@echo off

set TEST_NAME={path.test_name}
set TINC_PATH={path.tinc_path}
set TINCD_PATH={path.tincd_path}
set SPTPS_TEST_PATH={path.sptps_test_path}
set SPTPS_KEYPAIR_PATH={path.sptps_keypair_path}
set SPLICE_PATH={path.splice_path}

"{path.python_path}" {cmd} "{script}"
'''
