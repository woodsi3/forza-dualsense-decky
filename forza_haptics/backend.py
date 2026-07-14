from __future__ import annotations

import json
import logging
from pathlib import Path
import signal
import threading
import time

from .config import Settings
from .diagnostics import read_dualsense_battery
from .effects import EffectEngine
from .hidraw import DualSenseWriter
from .status import RuntimeStatus
from .telemetry import TelemetryReceiver
from .triggers import clear_effect, resistance, vibration


class Backend:
    def __init__(
        self,
        settings: Settings,
        settings_path: Path,
        status_path: Path,
        command_path: Path,
    ) -> None:
        self.settings = settings
        self.settings_path = settings_path
        self.status_path = status_path
        self.command_path = command_path
        self.stop_event = threading.Event()
        self.status = RuntimeStatus(enabled=settings.enabled)
        self.log = logging.getLogger("forza-haptics")
        self._settings_mtime_ns = self._mtime_ns(settings_path)
        self._last_command_id = ""
        self._test_name = ""
        self._test_until = 0.0
        self._settings_revision = 0

    @staticmethod
    def _mtime_ns(path: Path) -> int:
        try:
            return path.stat().st_mtime_ns
        except OSError:
            return 0

    def request_stop(self, *_: object) -> None:
        self.stop_event.set()

    def _reload_settings(self, engine: EffectEngine, controller: DualSenseWriter) -> None:
        mtime = self._mtime_ns(self.settings_path)
        if not mtime or mtime == self._settings_mtime_ns:
            return

        try:
            updated = Settings.load(self.settings_path)
        except (OSError, ValueError, json.JSONDecodeError) as exc:
            self.log.warning("Ignoring invalid live settings update: %s", exc)
            self._settings_mtime_ns = mtime
            return

        if (updated.udp_host, updated.udp_port) != (
            self.settings.udp_host,
            self.settings.udp_port,
        ):
            self.log.warning(
                "UDP host/port changed; restart engine to apply network changes"
            )

        self.settings = updated
        engine.settings = updated
        controller.reconnect_interval = updated.reconnect_interval
        controller.locked_serial = updated.controller_serial.replace(":", "").lower()
        self.status.enabled = updated.enabled
        self._settings_revision += 1
        self._settings_mtime_ns = mtime
        self.log.info("Applied live settings revision %d", self._settings_revision)

    def _read_command(self) -> dict | None:
        try:
            data = json.loads(self.command_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return None
        command_id = str(data.get("id", ""))
        if not command_id or command_id == self._last_command_id:
            return None
        self._last_command_id = command_id
        return data

    def _process_command(self) -> None:
        command = self._read_command()
        if not command:
            return
        if command.get("type") != "test_effect":
            self.log.warning("Unknown command: %s", command.get("type"))
            return
        effect = str(command.get("effect", ""))
        if effect not in {"pedal", "abs", "gear", "rev"}:
            self.log.warning("Unknown test effect: %s", effect)
            return
        self._test_name = effect
        self._test_until = time.monotonic() + 1.2
        self.log.info("Starting test effect: %s", effect)

    def _test_effects(self, now: float):
        if not self._test_name or now >= self._test_until:
            self._test_name = ""
            return None
        neutral = clear_effect()
        if self._test_name == "pedal":
            return resistance(0, 90), resistance(0, 90)
        if self._test_name == "abs":
            return vibration(35, 42, 22), neutral
        if self._test_name == "gear":
            return neutral, vibration(20, 90, 14)
        if self._test_name == "rev":
            return neutral, vibration(25, 60, 32)
        return None

    def _refresh_status(
        self,
        receiver: TelemetryReceiver,
        controller: DualSenseWriter,
        engine: EffectEngine,
        latest_state,
    ) -> None:
        now = time.monotonic()
        age = (
            now - receiver.last_packet_monotonic
            if receiver.last_packet_monotonic
            else None
        )
        telemetry_ok = age is not None and age <= self.settings.telemetry_stale_after

        self.status.running = not self.stop_event.is_set()
        self.status.enabled = self.settings.enabled
        self.status.telemetry = "receiving" if telemetry_ok else "waiting"
        self.status.telemetry_sender = receiver.last_sender
        self.status.packet_count = receiver.packet_count
        self.status.bad_packet_count = receiver.bad_packet_count
        self.status.packet_age_seconds = round(age, 3) if age is not None else None
        self.status.settings_revision = self._settings_revision
        self.status.active_test = self._test_name

        battery, battery_status = read_dualsense_battery()
        self.status.controller_battery_percent = battery
        self.status.controller_battery_status = battery_status

        if controller.connected and controller.info is not None:
            info = controller.info
            self.status.controller = "connected"
            self.status.controller_name = info.name
            self.status.controller_transport = info.transport
            self.status.controller_path = info.path
            self.status.controller_serial = info.serial
            self.status.controller_product_id = f"0x{info.product_id:04x}"
            self.status.controller_error = ""
        else:
            self.status.controller = "disconnected"
            self.status.controller_name = ""
            self.status.controller_transport = ""
            self.status.controller_path = ""
            self.status.controller_serial = ""
            self.status.controller_product_id = ""
            self.status.controller_error = controller.last_error

        self.status.brake_effect = engine.status.brake_mode
        self.status.throttle_effect = engine.status.throttle_mode

        if latest_state is not None:
            self.status.speed_kmh = round(latest_state.speed_kmh, 1)
            self.status.rpm = round(latest_state.engine_rpm, 0)
            self.status.rpm_ratio = round(latest_state.rpm_ratio, 3)
            self.status.gear = latest_state.gear

        self.status.write(self.status_path)

    def run(self) -> int:
        signal.signal(signal.SIGINT, self.request_stop)
        signal.signal(signal.SIGTERM, self.request_stop)

        engine = EffectEngine(self.settings)
        latest_state = None
        last_status_write = 0.0
        neutral = clear_effect()

        self.log.info(
            "Starting backend on UDP %s:%d",
            self.settings.udp_host,
            self.settings.udp_port,
        )

        try:
            with TelemetryReceiver(
                self.settings.udp_host,
                self.settings.udp_port,
                self.settings.udp_timeout,
            ) as receiver, DualSenseWriter(
                self.settings.reconnect_interval,
                self.settings.controller_serial,
            ) as controller:
                while not self.stop_event.is_set():
                    controller.connect_if_needed()
                    self._reload_settings(engine, controller)
                    self._process_command()
                    state = receiver.receive_latest()
                    now = time.monotonic()

                    test_effects = self._test_effects(now)
                    if test_effects is not None:
                        left, right = test_effects
                        controller.write(left, right)
                        engine.status.brake_mode = (
                            f"test {self._test_name}" if self._test_name in {"pedal", "abs"} else "clear"
                        )
                        engine.status.throttle_mode = (
                            f"test {self._test_name}" if self._test_name in {"pedal", "gear", "rev"} else "clear"
                        )
                    elif state is not None:
                        latest_state = state
                        left, right = engine.compute(state)
                        controller.write(left, right)
                    elif (
                        receiver.last_packet_monotonic
                        and now - receiver.last_packet_monotonic
                        > self.settings.telemetry_stale_after
                    ):
                        engine.status.brake_mode = "clear"
                        engine.status.throttle_mode = "clear"
                        controller.write(neutral, neutral)

                    if now - last_status_write >= self.settings.status_interval:
                        self._refresh_status(
                            receiver,
                            controller,
                            engine,
                            latest_state,
                        )
                        last_status_write = now

        except OSError as exc:
            self.log.error("Backend failed: %s", exc)
            self.status.running = False
            self.status.controller_error = str(exc)
            self.status.write(self.status_path)
            return 1
        finally:
            self.status.running = False
            self.status.brake_effect = "clear"
            self.status.throttle_effect = "clear"
            self.status.active_test = ""
            self.status.write(self.status_path)
            self.log.info("Backend stopped and trigger effects cleared")

        return 0
