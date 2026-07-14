#!/usr/bin/env python3
from pathlib import Path
import json

path = Path.home() / ".local" / "share" / "forza-dualsense" / "settings.json"
if not path.exists():
    raise SystemExit(f"Settings file not found: {path}")

data = json.loads(path.read_text(encoding="utf-8"))
data.update({
    "rev_limiter_ratio": 0.88,
    "rev_limiter_release_ratio": 0.84,
    "rev_limiter_min_throttle": 20,
    "rev_limiter_amplitude": 60,
})
path.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
print(f"Updated {path}")
