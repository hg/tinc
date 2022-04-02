#!/usr/bin/env python3

import typing as T

from .log import log
from .proc import Tinc

ExchangeIO = T.Tuple[
    T.Tuple[str, str],
    T.Tuple[str, str],
    T.Tuple[str, str],
]


def exchange(foo: Tinc, bar: Tinc, export_all: bool = False) -> ExchangeIO:
    """
    Runs `export(-all) | exchange | import` between the passed nodes.
    `export-all` is used if export_all is set to True.
    """
    export_cmd = 'export-all' if export_all else 'export'
    log.debug('doing %s between %s and %s', export_cmd, foo.name, bar.name)

    exp_out, exp_err = foo.cmd(export_cmd)
    log.debug('exchange: first peer returned ("%s", "%s")', exp_out, exp_err)
    assert 'Name =' in exp_out

    xch_out, xch_err = bar.cmd('exchange', stdin=exp_out)
    log.debug('exchange: second peer returned ("%s", "%s")', xch_out, xch_err)
    assert 'Name =' in xch_out
    assert 'Imported ' in xch_err

    imp_out, imp_err = foo.cmd('import', stdin=xch_out)
    log.debug('exchange: third peer returned ("%s", "%s")', imp_out, imp_err)
    assert 'Imported ' in imp_err

    return (
        (exp_out, exp_err),
        (xch_out, xch_err),
        (imp_out, imp_err),
    )
