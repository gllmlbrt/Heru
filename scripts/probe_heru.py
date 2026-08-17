#!/usr/bin/env python3
"""Probe a HERU Modbus bridge to find the working framer and unit ID.

The HERU Gen 3 speaks Modbus RTU over RS485, so it is normally reached through
a serial-to-TCP bridge. Those bridges come in two flavours: proper Modbus TCP
gateways (SOCKET framing) and transparent serial tunnels (RTU framing over
TCP). Sending the wrong framing, or addressing the wrong unit ID, produces no
reply at all rather than an error - which surfaces in Home Assistant as
"No response received after 3 retries".

This script tries every combination and reports which one answers.

Usage:
    pip install 'pymodbus>=3.10,<4'
    python3 scripts/probe_heru.py <host> [port]

Run it from any machine that can reach the bridge, then use the reported
framer and unit ID when adding the integration in Home Assistant.
"""

from __future__ import annotations

import asyncio
import sys

from pymodbus import FramerType
from pymodbus.client import AsyncModbusTcpClient

# 3x00001 "Component ID" always reads 10 on a HERU Gen 3, which makes it a
# reliable fingerprint that we are talking to the right device.
COMPONENT_ID_REGISTER = 0
EXPECTED_COMPONENT_ID = 10

FRAMERS = [("socket", FramerType.SOCKET), ("rtu", FramerType.RTU)]
UNIT_IDS = list(range(0, 11)) + [247]


async def probe(host: str, port: int, framer_name: str, framer, unit_id: int) -> str | None:
    """Try one framer/unit-ID combination, returning a result description."""
    client = AsyncModbusTcpClient(host, port=port, framer=framer, timeout=2, retries=1)
    try:
        if not await client.connect():
            return None
        response = await client.read_input_registers(
            address=COMPONENT_ID_REGISTER, count=1, device_id=unit_id
        )
        if response.isError():
            return f"error response ({response})"
        value = response.registers[0]
        if value == EXPECTED_COMPONENT_ID:
            return f"OK - Component ID {value} (HERU confirmed)"
        return f"replied, Component ID {value} (expected {EXPECTED_COMPONENT_ID})"
    except Exception as err:  # noqa: BLE001 - probing, report anything that goes wrong
        return f"{type(err).__name__}: {err}"
    finally:
        client.close()


async def main() -> int:
    """Run the probe across every framer and unit ID."""
    if len(sys.argv) < 2:
        print(__doc__)
        return 2

    host = sys.argv[1]
    port = int(sys.argv[2]) if len(sys.argv) > 2 else 502

    print(f"Probing {host}:{port}\n")
    hits: list[tuple[str, int]] = []

    for framer_name, framer in FRAMERS:
        print(f"--- framer: {framer_name} ---")
        for unit_id in UNIT_IDS:
            result = await probe(host, port, framer_name, framer, unit_id)
            if result is None:
                print(f"  unit {unit_id:>3}: TCP connect failed")
                continue
            print(f"  unit {unit_id:>3}: {result}")
            if result.startswith("OK"):
                hits.append((framer_name, unit_id))
        print()

    if hits:
        print("Working combination(s):")
        for framer_name, unit_id in hits:
            print(f"  framer={framer_name}  unit/device ID={unit_id}")
        print("\nUse these values when adding the Heru integration.")
        return 0

    print(
        "No combination answered.\n"
        "Check that the bridge is reachable on this host/port, that the RS485\n"
        "wiring (A/B polarity) and serial settings match the HERU, and that no\n"
        "other client is holding the bridge's single TCP connection open."
    )
    return 1


if __name__ == "__main__":
    raise SystemExit(asyncio.run(main()))
