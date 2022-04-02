#!/usr/bin/env python3

import typing as T


class Notification:
    """Notification about tinc script execution."""
    test: str
    node: str
    script: str
    env: T.Dict[str, str]
    args: T.Dict[str, str]
    error: T.Optional[Exception]
