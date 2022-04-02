#!/usr/bin/env python3

from .proc import Tinc
from .log import log


def nodes(node: Tinc, nodes: int) -> None:
    """Checks that node can reach exactly N nodes (including itself)."""
    log.info('want %d reachable nodes from tinc %s', nodes, node)
    stdout, _ = node.cmd('dump', 'reachable', 'nodes')
    assert len(stdout.splitlines()) == nodes


def files(path0: str, path1: str) -> None:
    """Compares file contents, ignoring whitespace at the beginning and at the end."""
    log.debug('comparing files %s and %s', path0, path1)

    def read(path: str) -> str:
        log.debug('reading file %s', path)
        with open(path, 'r') as f:
            return f.read().strip()

    content0 = read(path0)
    content1 = read(path1)

    if content0 != content1:
        log.error('expected files %s and %s to match', path0, path1)
        assert False
