#!/usr/bin/env python3

import os
import subprocess as subp

from testlib import log, path, util, check
from testlib.util import random_string

port = util.random_port()


class Keypair:
    private: str
    public: str

    def __init__(self, name: str):
        self.private = os.path.join(path.test_wd, f"{name}.priv")
        self.public = os.path.join(path.test_wd, f"{name}.pub")
        subp.run([path.sptps_keypair_path, self.private, self.public], check=True)


log.info("generate keys")
server_key = Keypair("server")
client_key = Keypair("client")

log.info("transfer random data")
data = random_string(256).encode("utf-8")


def run_single_test(key0: Keypair, key1: Keypair, *flags: str) -> None:
    cmd = [path.sptps_test_path, "-4", *flags, key0.private, key1.public, str(port)]
    log.info('start server with "%s"', " ".join(cmd))
    server = subp.Popen(cmd, stdout=subp.PIPE, stderr=subp.PIPE)

    while not server.stderr.readline().startswith(b"Listening..."):
        log.info("waiting for server to start accepting connections")

    cmd = [
        path.sptps_test_path,
        "-4",
        "-q",
        *flags,
        key1.private,
        key0.public,
        "localhost",
        str(port),
    ]
    log.info('start client with "%s"', " ".join(cmd))
    subp.run(cmd, input=data, check=True)

    received = b""
    while len(received) < len(data):
        received += server.stdout.read()

    if server.returncode is None:
        server.kill()

    check.equals(data, received)


def run_keypair_tests(*flags: str) -> None:
    log.info("running tests with (client, server) keypair and flags %s", flags)
    run_single_test(server_key, client_key)

    log.info("running tests with (server, client) keypair and flags %s", flags)
    run_single_test(client_key, server_key)


log.info("running tests in stream mode")
run_keypair_tests()

log.info("running tests in datagram mode")
run_keypair_tests("-dq")
