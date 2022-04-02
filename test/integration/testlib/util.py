#!/usr/bin/env python3

import os
import sys
import subprocess as subp
import socket
import random
import string

from .log import log
from .const import EXIT_SKIP


def random_string(k: int) -> str:
    return ''.join(random.choices(string.ascii_lowercase + string.digits, k=k))


def random_port() -> int:
    """
    Finds a random unused TCP port. Note that this function cannot 'hold' the port
    it returns, and it can be taken by something else before you manage to use it.
    """
    for _ in range(16):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(('localhost', 0))
                sock.listen()
                _, port = sock.getsockname()
                return port
        except OSError as e:
            log.error('could not bind to random port', port, exc_info=e)
    raise RuntimeError('could not bind to any port')


def find_line(filename: str, prefix: str) -> str:
    """
    Finds a line with the prefix in a text file.
    Checks that only one line matches.
    """
    with open(filename, 'r') as f:
        keylines = [line for line in f.readlines() if line.startswith(prefix)]
    assert len(keylines) == 1
    return keylines[0].rstrip()


def require_root() -> None:
    """
    Checks that test is running with root privileges.
    Exits with code 77 otherwise.
    """
    euid = os.geteuid()
    if euid:
        log.info('this test requires root privileges (you are running under UID %d)', euid)
        sys.exit(EXIT_SKIP)


def require_command(*args: str) -> None:
    """
    Checks that command args runs with exit code 0.
    Exits with code 77 otherwise.
    """
    if subp.run(args).returncode:
        log.info('this test requires command "%s" to work', ' '.join(args))
        sys.exit(EXIT_SKIP)


def require_path(path: str) -> None:
    """
    Checks that path exists in your file system.
    Exits with code 77 otherwise.
    """
    if not os.path.exists(path):
        log.warn('this test requires path %s to be present', path)
        sys.exit(EXIT_SKIP)
