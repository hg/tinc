#!/usr/bin/env python3

import asyncio

from testlib import Test, Script, Tinc, log, cmd, check


async def recv(read: asyncio.StreamReader, out: [bytes]) -> None:
    while True:
        rec = await read.read(4096)
        assert rec
        out.append(rec)


async def send(port: int, buf: str, delay: int = 0) -> bytes:
    raw = f"{buf}\n".encode("utf-8")
    read, write = await asyncio.open_connection(host="localhost", port=port)

    if delay:
        await asyncio.sleep(delay)

    received: [bytes] = []
    try:
        write.write(raw)
        await asyncio.wait_for(recv(read, received), timeout=1)
    except asyncio.TimeoutError:
        log.info('received: "%s"', received)
        return b"".join(received)


with Test("security") as t:
    foo, bar = t.node(), t.node()

    tarpit_timeout = 2

    null_metakey = f"""
0 {foo} 17.0\
1 0 672 0 0 834188619F4D943FD0F4B1336F428BD4AC06171FEABA66BD2356BC9593F0ECD643F\
0E4B748C670D7750DFDE75DC9F1D8F65AB1026F5ED2A176466FBA4167CC567A2085ABD070C1545B\
180BDA86020E275EA9335F509C57786F4ED2378EFFF331869B856DDE1C05C461E4EECAF0E2FB97A\
F77B7BC2AD1B34C12992E45F5D1254BBF0C3FB224ABB3E8859594A83B6CA393ED81ECAC9221CE6B\
C71A727BCAD87DD80FC0834B87BADB5CB8FD3F08BEF90115A8DF1923D7CD9529729F27E1B8ABD83\
C4CF8818AE10257162E0057A658E265610B71F9BA4B365A20C70578FAC65B51B91100392171BA12\
A440A5E93C4AA62E0C9B6FC9B68F953514AAA7831B4B2C31C4
""".strip()

    stdin = f"""
        init {foo}
        set DeviceType dummy
        set Port {foo.port}
        set Address localhost
        set PingTimeout {tarpit_timeout}
        set AutoConnect no
        set Subnet 10.96.96.1
    """
    foo.cmd(stdin=stdin)

    stdin = f"""
        init {bar}
        set DeviceType dummy
        set Port {bar.port}
        set PingTimeout {tarpit_timeout}
        set MaxTimeout {tarpit_timeout}
        set ExperimentalProtocol no
        set AutoConnect no
        set Subnet 10.96.96.2
    """
    bar.cmd(stdin=stdin)

    log.info("exchange host configs")
    cmd.exchange(foo, bar)

    foo.add_script(Script.SUBNET_UP)
    bar.add_script(Script.SUBNET_UP)
    foo.cmd("start")
    bar.cmd("start")
    foo[Script.SUBNET_UP].wait()
    bar[Script.SUBNET_UP].wait()

    id_bar = f"0 {bar} 17.7"
    id_foo = f"0 {foo} 17.7"
    id_baz = "0 baz 17.7"

    async def test_id_timeout():
        log.info(
            "no ID sent by responding node if we do not send an ID first before the timeout"
        )
        data = await send(foo.port, id_bar, delay=tarpit_timeout * 2)
        check.false(data)

    async def test_tarpitted():
        log.info("ID sent if initiator sends first, but still tarpitted")
        data = await send(foo.port, id_bar)
        assert data.startswith(id_foo.encode("utf-8"))

    async def test_invalid_id_foo():
        log.info("no invalid IDs allowed")
        data = await send(foo.port, id_foo)
        check.false(data)

    async def test_invalid_id_baz():
        log.info("no invalid IDs allowed")
        data = await send(foo.port, id_baz)
        check.false(data)

    async def test_null_metakey():
        log.info("no NULL METAKEY allowed")
        data = await send(foo.port, null_metakey)
        check.false(data)

    async def run_tests():
        await asyncio.gather(
            test_id_timeout(),
            test_tarpitted(),
            test_invalid_id_foo(),
            test_invalid_id_baz(),
            test_null_metakey(),
        )

    loop = asyncio.get_event_loop()
    loop.run_until_complete(run_tests())
