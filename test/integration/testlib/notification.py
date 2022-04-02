#!/usr/bin/env python3

import threading
import queue
import multiprocessing.connection as mp
import typing as T

from .log import log
from .path import test_name
from .event import Notification


def get_key(name, script):
    return f'{name}/{script}'


class NotificationServer:
    """Receives lifetime event notifications from tincd scripts."""
    port: int
    _lock: threading.Lock
    _ready: threading.Event
    _worker: T.Optional[threading.Thread]
    _notifications: T.Dict[str, queue.Queue]

    def __init__(self, port: int):
        self.port = port
        self._notifications = {}
        self._lock = threading.Lock()
        self._ready = threading.Event()
        self._worker = threading.Thread(target=self._recv, daemon=True)
        self._worker.start()

        log.debug('waiting for notification worker to become ready')
        self._ready.wait()
        log.debug('notification worker is ready')

    def get(self, name: str, script: str) -> Notification:
        key = get_key(name, script)
        with self._lock:
            q = self._notifications.get(key, queue.Queue())
            self._notifications[key] = q
        return q.get()

    def _recv(self) -> None:
        while True:
            try:
                self._listen()
            except Exception as e:
                log.error('recv notifications failed', exc_info=e)

    def _listen(self) -> None:
        with mp.Listener(('localhost', self.port)) as listener:
            self._ready.set()
            while True:
                with listener.accept() as conn:
                    self._handle_conn(conn)

    def _handle_conn(self, conn: mp.Connection) -> None:
        log.debug('accepted connection')

        data = conn.recv()
        assert isinstance(data, Notification)

        key = get_key(data.node, data.script)
        log.debug('from "%s" received data "%s"', key, data)

        if data.test != test_name:
            log.error('received notification for wrong test %s (wanted %s)', data.test, test_name)
            return

        with self._lock:
            q = self._notifications.get(key, queue.Queue())
            self._notifications[key] = q
        q.put(data)
