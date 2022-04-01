#!/usr/bin/env python3

import typing as T
from enum import Enum

from .path import test_name, python_path, cwd, test_src_root
from .notification import NotificationServer
from .util import random_port

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

    def __init__(self, name: str, script: str):
        self._name = name
        self._script = script

    def wait(self) -> T.Dict[str, str]:
        data = notifications.get(self._name, self._script)
        return data['env']


cwd = cwd.replace('\\', '/')
test_src_root = test_src_root.replace('\\', '/')

def make_script(script: str, name: str, source: str) -> str:
    return f'''#!{python_path}

import os
import sys
import multiprocessing.connection as mpc
import subprocess as subp
import typing as T
import logging
import time
 
os.chdir('{cwd}')
sys.path.append('{test_src_root}')

from testlib.proc import Tinc
from testlib.log import make_logger

this = Tinc('{name}')

log = make_logger('{name}')

def notify_test(args: T.Dict[str, T.Any] = {{}}):
    log.info(f'sending notification to port %d', {notifications.port})
    for retry in range(1, 5):
        try:
            with mpc.Client(('localhost', {notifications.port})) as conn:
                conn.send({{
                    **args,
                    'test': '{test_name}',
                    'name': '{name}',
                    'script': '{script}',
                    'env': dict(os.environ),
                }})
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
    notify_test({{ 'error': e }})
    sys.exit(1)

notify_test()
'''
