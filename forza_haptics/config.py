from __future__ import annotations

import json
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any


@dataclass
class Settings:
    udp_host: str = "0.0.0.0"
    udp_port: int = 5300
    udp_timeout: float = 0.25

    enabled: bool = True
    reconnect_interval: float = 2.0
    telemetry_stale_after: float = 1.0
    status_interval: float = 1.0

    pedal_force_intensity: float = 1.0
    abs_intensity: float = 1.0
    gear_kick_intensity: float = 1.0
    rev_limiter_intensity: float = 1.0
    traction_intensity: float = 1.0

    pedal_response_curve: str = "progressive"
    traction_response_curve: str = "progressive"

    traction_enabled: bool = True
    traction_min_throttle: int = 40
    traction_min_speed_kmh: float = 8.0
    traction_mild_slip: float = 0.22
    traction_heavy_slip: float = 0.55
    traction_max_extra_force: int = 90
    traction_pulse_amplitude: int = 48
    traction_pulse_frequency: int = 26

    automatic_car_profiles: bool = False

    brake_base_force: int = 26
    brake_max_force: int = 150
    throttle_base_force: int = 18
    throttle_max_force: int = 105

    abs_min_brake: int = 75
    abs_min_speed_kmh: float = 12.0
    abs_slip_threshold: float = 0.35
    abs_amplitude: int = 42
    abs_frequency: int = 22

    gear_kick_amplitude: int = 90
    gear_kick_frequency: int = 14
    gear_kick_duration_ms: float = 90.0

    # Forza can report max_rpm above the actual in-game limiter.
    rev_limiter_ratio: float = 0.88
    rev_limiter_release_ratio: float = 0.84
    rev_limiter_min_throttle: int = 20
    rev_limiter_amplitude: int = 60
    rev_limiter_frequency: int = 32

    controller_serial: str = ""
    debug: bool = False

    @classmethod
    def load(cls, path: Path) -> "Settings":
        defaults = cls()
        if not path.exists():
            path.parent.mkdir(parents=True, exist_ok=True)
            defaults.save(path)
            return defaults

        data = json.loads(path.read_text(encoding="utf-8"))
        allowed = defaults.__dict__.keys()
        clean: dict[str, Any] = {k: v for k, v in data.items() if k in allowed}
        settings = cls(**clean)
        settings.validate()
        return settings

    def save(self, path: Path) -> None:
        self.validate()
        path.parent.mkdir(parents=True, exist_ok=True)
        temp = path.with_suffix(path.suffix + ".tmp")
        temp.write_text(json.dumps(asdict(self), indent=2) + "\n", encoding="utf-8")
        temp.replace(path)

    def validate(self) -> None:
        if not 1 <= self.udp_port <= 65535:
            raise ValueError("udp_port must be between 1 and 65535")
        for name in (
            "pedal_force_intensity",
            "abs_intensity",
            "gear_kick_intensity",
            "rev_limiter_intensity",
            "traction_intensity",
        ):
            value = float(getattr(self, name))
            if not 0.0 <= value <= 2.0:
                raise ValueError(f"{name} must be between 0.0 and 2.0")
        for name in ("pedal_response_curve", "traction_response_curve"):
            if getattr(self, name) not in {"linear", "progressive", "aggressive"}:
                raise ValueError(f"{name} must be linear, progressive or aggressive")
        if self.traction_mild_slip < 0 or self.traction_heavy_slip <= self.traction_mild_slip:
            raise ValueError("traction slip thresholds are invalid")
        if not 0.5 <= self.rev_limiter_ratio <= 1.2:
            raise ValueError("rev_limiter_ratio must be between 0.5 and 1.2")
        if not 0.5 <= self.rev_limiter_release_ratio <= self.rev_limiter_ratio:
            raise ValueError(
                "rev_limiter_release_ratio must be between 0.5 and rev_limiter_ratio"
            )
