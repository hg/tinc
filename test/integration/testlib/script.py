#!/usr/bin/env python3

import os
import queue
from enum import Enum
import typing as T

from .log import log
from .event import Notification
from .notification import notifications


class Script(Enum):
    TINC_UP = "tinc-up"
    TINC_DOWN = "tinc-down"
    HOST_UP = "host-up"
    HOST_DOWN = "host-down"
    SUBNET_UP = "subnet-up"
    SUBNET_DOWN = "subnet-down"
    INVITATION_CREATED = "invitation-created"
    INVITATION_ACCEPTED = "invitation-accepted"


class TincScript:
    _node: str
    _path: str
    _script: str

    def __init__(self, node: str, script: str, path: str):
        self._node = node
        self._script = script
        self._path = path

    def wait(self, timeout: T.Optional[float] = None) -> T.Optional[Notification]:
        """
        Wait for the script to finish, returning the notification sent by the script.
        Returns None if timeout is specified and nothing was received during that time.
        """
        log.debug("waiting for script %s/%s", self._node, self._script)
        return notifications.get(self._node, self._script, timeout)

    @property
    def enabled(self) -> bool:
        return os.path.exists(self._path)

    def enable(self) -> None:
        log.debug("enabling script %s/%s", self._node, self._script)
        assert not self.enabled
        os.rename(self._disabled_name, self._path)

    def disable(self) -> None:
        log.debug("disabling script %s/%s", self._node, self._script)
        assert self.enabled
        os.rename(self._path, self._disabled_name)

    @property
    def _disabled_name(self):
        return f"{self._path}.disabled"
