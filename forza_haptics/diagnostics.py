from __future__ import annotations

from pathlib import Path


def read_dualsense_battery() -> tuple[int | None, str]:
    """Return battery percentage/status when hid-playstation exposes it."""
    roots = sorted(Path("/sys/class/power_supply").glob("sony_controller_battery_*"))
    for root in roots:
        try:
            capacity_text = (root / "capacity").read_text(encoding="utf-8").strip()
            status = (root / "status").read_text(encoding="utf-8").strip()
            return int(capacity_text), status
        except (OSError, ValueError):
            continue
    return None, "Unavailable"
