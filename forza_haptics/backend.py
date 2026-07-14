from __future__ import annotations

import logging
from pathlib import Path
import signal
import threading
import time

from .config import Settings
from .effects import EffectEngine
from .hidraw import DualSenseWriter
from .status import RuntimeStatus
from .telemetry import TelemetryReceiver
from .triggers import clear_effect


class Backend:
    def __init__(self, settings: Settings, status_path: Path) -> None:
        self.settings = settings
        self.status_path = status_path
        self.stop_event = threading.Event()
        self.status = RuntimeStatus(enabled=settings.enabled)
        self.log = logging.getLogger("forza-haptics")

    def request_stop(self, *_: object) -> None:
        self.stop_event.set()

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

        if controller.connected and controller.info is not None:
            self.status.controller = "connected"
            self.status.controller_name = controller.info.name
            self.status.controller_transport = controller.info.transport
            self.status.controller_path = controller.info.path
            self.status.controller_error = ""
        else:
            self.status.controller = "disconnected"
            self.status.controller_name = ""
            self.status.controller_transport = ""
            self.status.controller_path = ""
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
                    state = receiver.receive_latest()
                    now = time.monotonic()

                    if state is not None:
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
            self.status.write(self.status_path)
            self.log.info("Backend stopped and trigger effects cleared")

        return 0
