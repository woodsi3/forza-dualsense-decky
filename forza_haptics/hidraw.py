from __future__ import annotations

import glob
import os
import struct
import threading
import time
import zlib
from dataclasses import dataclass

from .triggers import TriggerEffect, clear_effect


SONY_VENDOR = 0x054C
PRODUCT_IDS = {0x0CE6: "DualSense", 0x0DF2: "DualSense Edge"}
FLAG_TRIGGERS = 0x04 | 0x08
_BT_CRC_INIT = zlib.crc32(b"\xA2")


@dataclass(frozen=True)
class Layout:
    report_id: int
    flags_offset: int
    right_trigger_offset: int
    left_trigger_offset: int
    report_length: int
    bluetooth: bool


USB = Layout(0x02, 1, 11, 22, 64, False)
BLUETOOTH = Layout(0x31, 2, 12, 23, 78, True)


@dataclass(frozen=True)
class DeviceInfo:
    path: str
    bus: int
    product_id: int
    serial: str

    @property
    def bluetooth(self) -> bool:
        return self.bus == 0x05

    @property
    def transport(self) -> str:
        return "Bluetooth" if self.bluetooth else "USB"

    @property
    def name(self) -> str:
        return PRODUCT_IDS.get(self.product_id, f"Sony 0x{self.product_id:04x}")


def _read_device(node: str) -> DeviceInfo | None:
    uevent = f"/sys/class/hidraw/{os.path.basename(node)}/device/uevent"
    try:
        fields: dict[str, str] = {}
        with open(uevent, encoding="utf-8") as handle:
            for line in handle:
                if "=" in line:
                    key, value = line.rstrip().split("=", 1)
                    fields[key] = value
        bus_s, vendor_s, product_s = fields["HID_ID"].split(":")
        bus = int(bus_s, 16)
        vendor = int(vendor_s, 16)
        product = int(product_s, 16)
    except (OSError, KeyError, ValueError):
        return None

    if vendor != SONY_VENDOR or product not in PRODUCT_IDS:
        return None

    return DeviceInfo(
        path=node,
        bus=bus,
        product_id=product,
        serial=fields.get("HID_UNIQ", "").replace(":", "").lower(),
    )


def enumerate_devices() -> list[DeviceInfo]:
    devices = [info for node in sorted(glob.glob("/dev/hidraw*"))
               if (info := _read_device(node)) is not None]
    wired_serials = {d.serial for d in devices if d.serial and not d.bluetooth}
    return [
        d for d in devices
        if not (d.bluetooth and d.serial and d.serial in wired_serials)
    ]


def assemble_report(
    layout: Layout,
    left: TriggerEffect,
    right: TriggerEffect,
) -> bytes:
    buffer = bytearray(layout.report_length)
    buffer[0] = layout.report_id
    if layout.bluetooth:
        buffer[1] = 0x02

    buffer[layout.flags_offset] = FLAG_TRIGGERS
    buffer[
        layout.right_trigger_offset:layout.right_trigger_offset + 11
    ] = right.pack()
    buffer[
        layout.left_trigger_offset:layout.left_trigger_offset + 11
    ] = left.pack()

    if layout.bluetooth:
        crc = zlib.crc32(memoryview(buffer)[:74], _BT_CRC_INIT)
        struct.pack_into("<I", buffer, 74, crc)

    return bytes(buffer)


class DualSenseWriter:
    def __init__(self, reconnect_interval: float = 2.0, serial: str = "") -> None:
        self.reconnect_interval = reconnect_interval
        self.locked_serial = serial.replace(":", "").lower()
        self.fd: int | None = None
        self.info: DeviceInfo | None = None
        self.layout = USB
        self.last_error = ""
        self.last_connect_attempt = 0.0
        self._lock = threading.Lock()

    @property
    def connected(self) -> bool:
        return self.fd is not None and self.info is not None

    def _choose(self) -> DeviceInfo | None:
        devices = enumerate_devices()
        if self.locked_serial:
            return next((d for d in devices if d.serial == self.locked_serial), None)
        return devices[0] if devices else None

    def connect_if_needed(self) -> bool:
        if self.connected:
            return True

        now = time.monotonic()
        if now - self.last_connect_attempt < self.reconnect_interval:
            return False
        self.last_connect_attempt = now

        target = self._choose()
        if target is None:
            self.last_error = "No compatible DualSense detected"
            return False

        try:
            fd = os.open(target.path, os.O_RDWR | os.O_NONBLOCK)
        except OSError as exc:
            self.last_error = f"Cannot open {target.path}: {exc}"
            return False

        with self._lock:
            self.fd = fd
            self.info = target
            self.layout = BLUETOOTH if target.bluetooth else USB
            self.last_error = ""
        return True

    def write(self, left: TriggerEffect, right: TriggerEffect) -> bool:
        if not self.connect_if_needed():
            return False

        report = assemble_report(self.layout, left, right)
        try:
            with self._lock:
                if self.fd is None:
                    return False
                written = os.write(self.fd, report)
            if written != len(report):
                raise OSError(f"short HID write {written}/{len(report)}")
            return True
        except OSError as exc:
            self.last_error = str(exc)
            self.disconnect(send_clear=False)
            return False

    def clear(self) -> None:
        neutral = clear_effect()
        self.write(neutral, neutral)

    def disconnect(self, send_clear: bool = True) -> None:
        with self._lock:
            fd = self.fd
            layout = self.layout
            self.fd = None
            self.info = None

        if fd is None:
            return
        if send_clear:
            try:
                os.write(fd, assemble_report(layout, clear_effect(), clear_effect()))
            except OSError:
                pass
        try:
            os.close(fd)
        except OSError:
            pass

    def close(self) -> None:
        self.disconnect(send_clear=True)

    def __enter__(self) -> "DualSenseWriter":
        self.connect_if_needed()
        return self

    def __exit__(self, *_: object) -> None:
        self.close()
