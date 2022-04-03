#!/usr/bin/env python3

import os
import sys
import subprocess as subp
import socket
import random
import string

from . import check
from .log import log
from .const import EXIT_SKIP

alnum = string.ascii_lowercase + string.digits


def random_string(k: int) -> str:
    """Generates a random alphanumeric string of length k."""
    return "".join(random.choices(alnum, k=k))


def random_port() -> int:
    """
    Finds a random unused TCP port. Note that this function cannot 'hold' the port
    it returns, and it can be taken by something else before you manage to use it.
    """
    for _ in range(16):
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.bind(("localhost", 0))
                sock.listen()
                _, port = sock.getsockname()
                return port
        except OSError as e:
            log.error("could not bind to random port", port, exc_info=e)
    raise RuntimeError("could not bind to any port")


def find_line(filename: str, prefix: str) -> str:
    """
    Finds a line with the prefix in a text file.
    Checks that only one line matches.
    """
    with open(filename, "r") as f:
        keylines = [line for line in f.readlines() if line.startswith(prefix)]
    check.equals(1, len(keylines))
    return keylines[0].rstrip()


def require_root() -> None:
    """
    Checks that test is running with root privileges.
    Exits with code 77 otherwise.
    """
    euid = os.geteuid()
    if euid:
        log.info("this test requires root (but running under UID %d)", euid)
        sys.exit(EXIT_SKIP)


def require_command(*args: str) -> None:
    """
    Checks that command args runs with exit code 0.
    Exits with code 77 otherwise.
    """
    if subp.run(args).returncode:
        log.info('this test requires command "%s" to work', " ".join(args))
        sys.exit(EXIT_SKIP)


def require_path(path: str) -> None:
    """
    Checks that path exists in your file system.
    Exits with code 77 otherwise.
    """
    if not os.path.exists(path):
        log.warn("this test requires path %s to be present", path)
        sys.exit(EXIT_SKIP)


# Thin wrappers around `with open(...) as f: f.do_something()`
# Don't do much, besides saving quite a bit of space because of how frequently they're needed.


def read_text(path: str) -> str:
    """Returns the text contents of a file."""
    with open(path) as f:
        return f.read()


def write_text(path: str, text: str) -> str:
    """Writes text to a file, replacing its content. Returns the text added."""
    with open(path, "w") as f:
        f.write(text)
    return text


def read_lines(path: str) -> [str]:
    """Reads file as a list of lines."""
    with open(path) as f:
        return f.read().splitlines()


def write_lines(path: str, lines: [str]) -> [str]:
    """Write text lines to a file, replacing it content. Returns the line added."""
    with open(path, "w") as f:
        f.write(os.linesep.join(lines))
        f.write(os.linesep)
    return lines


def append_line(path: str, line: str) -> str:
    """Appends a line to the end of the file. Returns the line added."""
    line = f"{os.linesep}{line}{os.linesep}"
    with open(path, "a") as f:
        f.write(line)
    return line
