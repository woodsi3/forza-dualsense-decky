from __future__ import annotations

import socket
import struct
import time
from dataclasses import dataclass


EXPECTED_PACKET_SIZE = 324


@dataclass(frozen=True)
class VehicleState:
    is_racing: bool
    timestamp_ms: int
    max_rpm: float
    idle_rpm: float
    engine_rpm: float
    tire_slip_ratio: tuple[float, float, float, float]
    tire_combined_slip: tuple[float, float, float, float]
    speed_mps: float
    throttle: int
    brake: int
    handbrake: int
    gear: int

    @property
    def speed_kmh(self) -> float:
        return self.speed_mps * 3.6

    @property
    def rpm_ratio(self) -> float:
        return self.engine_rpm / self.max_rpm if self.max_rpm > 1.0 else 0.0


def decode_packet(raw: bytes) -> VehicleState:
    if len(raw) != EXPECTED_PACKET_SIZE:
        raise ValueError(f"expected {EXPECTED_PACKET_SIZE} bytes, got {len(raw)}")

    on_flag, timestamp_ms, max_rpm, idle_rpm, engine_rpm = struct.unpack_from(
        "<iIfff", raw, 0
    )
    slip_ratio = struct.unpack_from("<4f", raw, 84)
    combined_slip = struct.unpack_from("<4f", raw, 180)
    speed_mps = struct.unpack_from("<f", raw, 256)[0]

    return VehicleState(
        is_racing=on_flag != 0,
        timestamp_ms=timestamp_ms,
        max_rpm=max_rpm,
        idle_rpm=idle_rpm,
        engine_rpm=engine_rpm,
        tire_slip_ratio=slip_ratio,
        tire_combined_slip=combined_slip,
        speed_mps=speed_mps,
        throttle=raw[315],
        brake=raw[316],
        handbrake=raw[318],
        gear=raw[319],
    )


class TelemetryReceiver:
    def __init__(self, host: str, port: int, timeout: float) -> None:
        self.host = host
        self.port = port
        self.timeout = timeout
        self.socket: socket.socket | None = None
        self.packet_count = 0
        self.bad_packet_count = 0
        self.last_packet_monotonic = 0.0
        self.last_sender = ""

    def open(self) -> None:
        sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 65536)
        sock.bind((self.host, self.port))
        sock.settimeout(self.timeout)
        self.socket = sock

    def close(self) -> None:
        if self.socket is not None:
            self.socket.close()
            self.socket = None

    def receive_latest(self) -> VehicleState | None:
        if self.socket is None:
            raise RuntimeError("receiver is not open")

        try:
            raw, address = self.socket.recvfrom(2048)
        except socket.timeout:
            return None

        self.socket.setblocking(False)
        try:
            while True:
                raw, address = self.socket.recvfrom(2048)
        except BlockingIOError:
            pass
        finally:
            self.socket.setblocking(True)
            self.socket.settimeout(self.timeout)

        if len(raw) != EXPECTED_PACKET_SIZE:
            self.bad_packet_count += 1
            return None

        try:
            state = decode_packet(raw)
        except (ValueError, struct.error):
            self.bad_packet_count += 1
            return None

        self.packet_count += 1
        self.last_packet_monotonic = time.monotonic()
        self.last_sender = f"{address[0]}:{address[1]}"
        return state

    def __enter__(self) -> "TelemetryReceiver":
        self.open()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
