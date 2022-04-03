#!/usr/bin/env python3

import subprocess as subp
import atexit

from .log import log

_netns_created = set()


def _netns_cleanup() -> None:
    for ns in _netns_created.copy():
        try:
            netns_delete(ns)
        except Exception as e:
            log.error("error deleting netns %s", ns, exc_info=e)


atexit.register(_netns_cleanup)


def netns_delete(ns: str) -> None:
    log.info("delete network namespace %s", ns)
    subp.run(["ip", "netns", "delete", ns], check=True)
    _netns_created.remove(ns)


def netns_add(ns: str) -> None:
    """Adds a network namespace. Registers a handler to destroy it on exit."""
    log.info("create network namespace %s", ns)
    subp.run(["ip", "netns", "add", ns], check=True)
    _netns_created.add(ns)
