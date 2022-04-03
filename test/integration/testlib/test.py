#!/usr/bin/env python3

import typing as T

from .log import log
from .proc import Tinc


class Test:
    """
    Test context. Allows you to obtain Tinc instances which are automatically
    stopped (and killed if necessary) at __exit__. Should be wrapped in `with`
    statements (like the built-in `open`). Should not be used too much (because
    of Windows, as usual: service registration and removal is quite slow, which
    makes tests take a long time to finish, especially on modest CI machines).
    """

    name: str
    _nodes: T.List[Tinc]

    def __init__(self, name: str):
        self._nodes = []
        self.name = name

    def node(self):
        node = Tinc()
        self._nodes.append(node)
        return node

    def __str__(self):
        return self.name

    def __enter__(self):
        log.info("RUNNING TEST: %s", self.name)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        for node in self._nodes:
            try:
                node.cleanup()
            except Exception as e:
                log.error("could not terminate node %s", node, exc_info=e)
        log.info("FINISHED TEST: %s", self.name)
