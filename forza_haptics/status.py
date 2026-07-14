from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
import time


@dataclass
class RuntimeStatus:
    running: bool = False
    enabled: bool = True
    telemetry: str = "waiting"
    telemetry_sender: str = ""
    packet_count: int = 0
    bad_packet_count: int = 0
    packet_age_seconds: float | None = None
    packet_rate_hz: float = 0.0
    controller: str = "disconnected"
    controller_name: str = ""
    controller_transport: str = ""
    controller_path: str = ""
    controller_serial: str = ""
    controller_product_id: str = ""
    controller_firmware: str = "Unavailable through hidraw"
    controller_battery_percent: int | None = None
    controller_battery_status: str = "Unavailable"
    controller_error: str = ""
    brake_effect: str = "clear"
    throttle_effect: str = "clear"
    active_test: str = ""
    settings_revision: int = 0
    speed_kmh: float = 0.0
    rpm: float = 0.0
    rpm_ratio: float = 0.0
    gear: int = 0
    abs_active: bool = False
    traction_state: str = "stable"
    rear_slip: float = 0.0
    surface_state: str = "unknown"
    car_ordinal: int = 0
    car_class: int = 0
    car_performance_index: int = 0
    active_profile: str = "Global"
    updated_unix: float = 0.0

    def write(self, path: Path) -> None:
        self.updated_unix = time.time()
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)
