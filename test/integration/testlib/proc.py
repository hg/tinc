#!/usr/bin/env python3

import os
import typing as T
import subprocess as subp
from enum import Enum

from . import check
from .log import log
from .path import test_wd, tinc_path, tincd_path
from .script import TincScript, Script
from .template import make_script, make_cmd_wrap
from .util import random_port, random_string


def _make_wd(name: str) -> str:
    path = os.path.join(test_wd, "data", name)
    os.makedirs(path, exist_ok=True)
    return path


class Feature(Enum):
    COMP_LZ4 = "comp_lz4"
    COMP_LZO = "comp_lzo"
    COMP_ZLIB = "comp_zlib"
    CURSES = "curses"
    JUMBOGRAMS = "jumbograms"
    LEGACY_PROTOCOL = "legacy_protocol"
    LIBGCRYPT = "libgcrypt"
    MINIUPNPC = "miniupnpc"
    OPENSSL = "openssl"
    READLINE = "readline"
    TUNEMU = "tunemu"
    UML = "uml"
    VDE = "vde"


class Tinc:
    name: str
    port: int
    wd: str
    _scripts: T.Dict[str, TincScript]
    _procs: T.List[subp.Popen]

    def __init__(self, name: str = ""):
        self.name = name if name else random_string(10)
        self.port = random_port()
        self.wd = _make_wd(self.name)
        self._scripts = {}
        self._procs = []

    def __str__(self):
        return self.name

    def __getitem__(self, script: T.Union[Script, str]) -> TincScript:
        if isinstance(script, Script):
            script = script.name
        return self._scripts[script]

    @property
    def features(self) -> [Feature]:
        tinc, _ = self.cmd("--version")
        tincd, _ = self.tincd("--version").communicate(timeout=5)
        prefix, features = "Features: ", []

        for out in (tinc, tincd):
            for line in out.splitlines():
                if not line.startswith(prefix):
                    continue
                tokens = line[len(prefix) :].split()
                for token in tokens:
                    features.append(Feature(token))
                break

        log.info('supported features: "%s"', features)
        return features

    @property
    def _common_args(self) -> [str]:
        return ["--net", self.name, "--config", self.wd, "--pidfile", self.sub("pid")]

    def sub(self, *paths: str) -> str:
        return os.path.join(self.wd, *paths)

    @property
    def script_up(self) -> str:
        return f"hosts/{self.name}-up"

    @property
    def script_down(self) -> str:
        return f"hosts/{self.name}-down"

    def cleanup(self):
        """Terminates all tinc and tincd processes started from this instance."""
        log.info("running node cleanup for %s", self)

        try:
            self.cmd("stop")
        except AssertionError:
            log.info("unsuccessfully tried to stop node %s", self)

        for proc in self._procs:
            if proc.returncode is not None:
                log.debug("PID %d exited, skipping", proc.pid)
            else:
                log.info("PID %d still running, stopping", proc.pid)
                try:
                    proc.kill()
                    proc.wait()
                except Exception as e:
                    log.error("could not kill PID %d", proc.pid, exc_info=e)

        self._procs.clear()

    def cmd(
        self, *args: str, code: T.Optional[int] = 0, stdin: T.Optional[str] = None
    ) -> T.Tuple[str, str]:
        """
        Runs command through tinc, writes `stdin` to it (if the argument is not None), checks
        its return code (if the `code` argument is not None), and returns (stdout, stderr).
        """
        proc = self.tinc(*args)
        log.debug('tinc %s: PID %d, in "%s", want code %d', self, proc.pid, stdin, code)

        out, err = proc.communicate(stdin, timeout=60)
        exit = proc.returncode
        self._procs.remove(proc)
        log.debug('tinc %s: code %d, out "%s", err "%s"', self, exit, out, err)

        if code is not None:
            check.equals(code, exit)

        return out if out else "", err if err else ""

    def tinc(self, *args: str):
        args = list(filter(bool, args))
        cmd = [tinc_path, *self._common_args, *args]
        log.debug('starting tinc %s: "%s"', self.name, " ".join(cmd))
        proc = subp.Popen(
            cmd,
            cwd=self.wd,
            stdin=subp.PIPE,
            stdout=subp.PIPE,
            stderr=subp.PIPE,
            encoding="utf-8",
        )
        self._procs.append(proc)
        return proc

    def tincd(self, *args: str, env: T.Optional[T.Dict[str, str]] = None) -> subp.Popen:
        args = list(filter(bool, args))
        cmd = [
            tincd_path,
            *self._common_args,
            "--logfile",
            self.sub("log"),
            "-d5",
            *args,
        ]
        log.debug('starting tincd %s: "%s"', self.name, " ".join(cmd))
        if env is not None:
            env = {**os.environ, **env}
        proc = subp.Popen(
            cmd,
            cwd=self.wd,
            stdin=subp.PIPE,
            stdout=subp.PIPE,
            stderr=subp.PIPE,
            encoding="utf-8",
            env=env,
        )
        self._procs.append(proc)
        return proc

    def add_script(self, script: T.Union[Script, str], source: str = "") -> TincScript:
        rel_path = script if isinstance(script, str) else script.value
        check.not_in(rel_path, self._scripts)

        full_path = os.path.join(self.wd, rel_path)
        ts = TincScript(self.name, rel_path, full_path)

        with open(full_path, "w") as f:
            content = make_script(self.name, rel_path, source)
            f.write(content)

        if os.name == "nt":
            with open(f"{full_path}.cmd", "w") as f:
                win_content = make_cmd_wrap(full_path)
                f.write(win_content)
        else:
            os.chmod(full_path, 0o755)

        if isinstance(script, Script):
            self._scripts[script.name] = ts
        self._scripts[rel_path] = ts

        return ts
