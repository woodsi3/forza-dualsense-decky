from __future__ import annotations

from enum import IntEnum
from typing import NamedTuple


class Mode(IntEnum):
    CLEAR = 0x05
    SIMPLE_RESISTANCE = 0x01
    SIMPLE_VIBRATION = 0x06


class TriggerEffect(NamedTuple):
    mode: int
    payload: bytes

    def pack(self) -> bytes:
        output = bytearray(11)
        output[0] = self.mode & 0xFF
        payload = self.payload[:10]
        output[1:1 + len(payload)] = payload
        return bytes(output)


def _u8(value: float | int) -> int:
    return max(0, min(255, int(round(value))))


def clear_effect() -> TriggerEffect:
    return TriggerEffect(Mode.CLEAR, b"")


def resistance(position: int, force: int) -> TriggerEffect:
    return TriggerEffect(
        Mode.SIMPLE_RESISTANCE,
        bytes((_u8(position), _u8(force))),
    )


def vibration(position: int, amplitude: int, frequency: int) -> TriggerEffect:
    return TriggerEffect(
        Mode.SIMPLE_VIBRATION,
        bytes((_u8(frequency), _u8(amplitude), _u8(position))),
    )
