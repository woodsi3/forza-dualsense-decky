from __future__ import annotations

import argparse
from dataclasses import asdict
import json
import logging
from pathlib import Path
import sys
import time

from .backend import Backend
from .config import Settings
from .hidraw import DualSenseWriter, enumerate_devices
from .triggers import clear_effect, resistance, vibration


DEFAULT_DATA_DIR = Path.home() / ".local" / "share" / "forza-dualsense"
DEFAULT_CONFIG = DEFAULT_DATA_DIR / "settings.json"
DEFAULT_STATUS = DEFAULT_DATA_DIR / "status.json"


def setup_logging(debug: bool) -> None:
    logging.basicConfig(
        level=logging.DEBUG if debug else logging.INFO,
        format="%(asctime)s %(levelname)s %(message)s",
    )


def controller_test(settings: Settings) -> int:
    devices = enumerate_devices()
    if not devices:
        print("[FAIL] No DualSense or DualSense Edge detected")
        return 1

    for index, device in enumerate(devices):
        print(
            f"[{index}] {device.name} {device.transport} "
            f"{device.path} serial={device.serial or 'unknown'}"
        )

    neutral = clear_effect()
    with DualSenseWriter(settings.reconnect_interval, settings.controller_serial) as writer:
        if not writer.connected:
            print(f"[FAIL] {writer.last_error}")
            return 1

        print("[TEST] L2 resistance")
        writer.write(resistance(0, 75), neutral)
        time.sleep(0.7)
        writer.clear()

        print("[TEST] R2 resistance")
        writer.write(neutral, resistance(0, 75))
        time.sleep(0.7)
        writer.clear()

        print("[TEST] Both-trigger vibration")
        buzz = vibration(40, 30, 180)
        writer.write(buzz, buzz)
        time.sleep(0.35)
        writer.clear()

    print("[PASS] Controller output test complete")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Forza DualSense SteamOS backend")
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--status", type=Path, default=DEFAULT_STATUS)
    parser.add_argument("--command-file", type=Path, default=DEFAULT_DATA_DIR / "command.json")

    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("run", help="Run the telemetry-to-trigger backend")
    sub.add_parser("init-config", help="Create a default settings file")
    sub.add_parser("show-config", help="Print the effective settings")
    sub.add_parser("controller-test", help="Test direct DualSense output")
    sub.add_parser("status", help="Print the latest runtime status")

    args = parser.parse_args()

    if args.command == "init-config":
        settings = Settings()
        settings.save(args.config)
        print(args.config)
        return 0

    if args.command == "status":
        if not args.status.exists():
            print("No status file yet")
            return 1
        print(args.status.read_text(encoding="utf-8"), end="")
        return 0

    try:
        settings = Settings.load(args.config)
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(f"Invalid config: {exc}", file=sys.stderr)
        return 2

    setup_logging(settings.debug)

    if args.command == "show-config":
        print(json.dumps(asdict(settings), indent=2))
        return 0
    if args.command == "controller-test":
        return controller_test(settings)
    if args.command == "run":
        return Backend(settings, args.config, args.status, args.command_file).run()

    return 2


if __name__ == "__main__":
    raise SystemExit(main())
