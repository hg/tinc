#!/usr/bin/env python3

import typing as T

from .log import log


def false(value: T.Any) -> None:
    """Checks that value is falsy."""
    if value:
        log.error('expected "%s" to be falsy')
        assert False


def true(value: T.Any) -> None:
    """Checks that value is truthy."""
    if not value:
        log.error('expected "%s" to be truthy', value)
        assert False


def equals(expected: T.Any, actual: T.Any) -> None:
    """Checks that the two values are equal."""
    if expected != actual:
        log.error('expected "%s", got "%s"', expected, actual)
        assert False


def in_(needle: T.Any, *haystacks: T.Iterable) -> None:
    """Checks that at least one haystack includes needle."""
    for hs in haystacks:
        if needle in hs:
            return
    log.error('expected any of "%s" to include "%s"', haystacks, needle)
    assert False


def not_in(needle: T.Any, *haystacks: T.Any) -> None:
    """Checks that all haystacks do not include needle."""
    for hs in haystacks:
        if needle in hs:
            log.error('expected all "%s" NOT to include "%s"', haystacks, needle)
            assert False


def nodes(node, nodes: int) -> None:
    """Checks that node can reach exactly N nodes (including itself)."""
    log.debug('want %d reachable nodes from tinc %s', nodes, node)
    stdout, _ = node.cmd('dump', 'reachable', 'nodes')
    equals(nodes, len(stdout.splitlines()))


def files_eq(path0: str, path1: str) -> None:
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
