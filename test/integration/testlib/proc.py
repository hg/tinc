#!/usr/bin/env python3

import os
import typing as T
import subprocess as subp

from . import check
from .log import log
from .path import test_wd, tinc_path, tincd_path
from .script import TincScript, Script, make_script, make_cmd_wrap
from .util import random_port, random_string


def make_wd(name: str) -> str:
    path = os.path.join(test_wd, 'data', name)
    os.makedirs(path, exist_ok=True)
    return path


class Tinc:
    name: str
    port: int
    wd: str
    _scripts: T.Dict[str, TincScript]

    def __init__(self, name: str = ''):
        self.name = name if name else random_string(10)
        self.port = random_port()
        self.wd = make_wd(self.name)
        self._scripts = {}

    def __str__(self):
        return self.name

    def __getitem__(self, script: T.Union[Script, str]) -> TincScript:
        if isinstance(script, Script):
            script = script.name
        return self._scripts[script]

    @property
    def _common_args(self) -> [str]:
        return ['--net', self.name,
                '--config', self.wd,
                '--pidfile', self.sub('pid')]

    def sub(self, *paths: str) -> str:
        return os.path.join(self.wd, *paths)

    @property
    def script_up(self) -> str:
        return f'hosts/{self.name}-up'

    @property
    def script_down(self) -> str:
        return f'hosts/{self.name}-down'

    def cmd(self, *args: str,
            code: T.Optional[int] = 0,
            stdin: T.Optional[str] = None) -> T.Tuple[str, str]:
        """
        Runs command through tinc, writes `stdin` to it (if the argument is not None), checks
        its return code (if the `code` argument is not None), and returns (stdout, stderr).
        """
        proc = self.tinc(*args)
        log.debug('tinc %s (PID %d): stdin "%s", want code %d', self.name, proc.pid, stdin, code)

        out, err = proc.communicate(stdin, timeout=60)
        log.debug('tinc %s finished: code %d, stdout "%s", stderr "%s"', self.name, proc.returncode, out, err)

        if code is not None:
            check.equals(code, proc.returncode)

        return out if out else '', err if err else ''

    def tinc(self, *args: str):
        args = list(filter(bool, args))
        cmd = [tinc_path, *self._common_args, *args]
        log.debug('starting tinc %s: "%s"', self.name, ' '.join(cmd))
        return subp.Popen(cmd, cwd=self.wd, stdin=subp.PIPE, stdout=subp.PIPE, stderr=subp.PIPE, encoding='utf-8')

    def tincd(self, *args: str) -> subp.Popen:
        args = list(filter(bool, args))
        cmd = [tincd_path, *self._common_args, '--logfile', self.sub('log'), '-d5', *args]
        log.debug('starting tincd %s: "%s"', self.name, ' '.join(cmd))
        return subp.Popen(cmd, cwd=self.wd, stdin=subp.PIPE, stdout=subp.PIPE, stderr=subp.PIPE, encoding='utf-8')

    def add_script(self, script: T.Union[Script, str], source: str = '') -> TincScript:
        rel_path = script if isinstance(script, str) else script.value
        check.not_in(rel_path, self._scripts)

        full_path = os.path.join(self.wd, rel_path)
        ts = TincScript(self.name, rel_path, full_path)

        with open(full_path, 'w') as f:
            content = make_script(self.name, rel_path, source)
            f.write(content)

        if os.name == 'nt':
            with open(f'{full_path}.cmd', 'w') as f:
                win_content = make_cmd_wrap(full_path)
                f.write(win_content)
        else:
            os.chmod(full_path, 0o755)

        if isinstance(script, Script):
            self._scripts[script.name] = ts
        self._scripts[rel_path] = ts

        return ts
