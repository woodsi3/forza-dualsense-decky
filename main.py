from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
import signal
import sys
from typing import Any

import decky


PLUGIN_DIR = Path(__file__).resolve().parent
SETTINGS_PATH = Path(decky.DECKY_SETTINGS_DIR) / "forza-dualsense-settings.json"
STATUS_PATH = Path(decky.DECKY_RUNTIME_DIR) / "forza-dualsense-status.json"
EXAMPLE_SETTINGS = PLUGIN_DIR / "settings.example.json"
ALLOWED_CONTROLS = {
    "enabled",
    "pedal_force_intensity",
    "abs_intensity",
    "gear_kick_intensity",
    "rev_limiter_intensity",
}


class Plugin:
    process: asyncio.subprocess.Process | None = None
    process_lock: asyncio.Lock

    async def _ensure_settings(self) -> None:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)
        if not SETTINGS_PATH.exists():
            SETTINGS_PATH.write_text(
                EXAMPLE_SETTINGS.read_text(encoding="utf-8"),
                encoding="utf-8",
            )

    async def _start_backend(self) -> bool:
        async with self.process_lock:
            if self.process is not None and self.process.returncode is None:
                return True

            await self._ensure_settings()
            command = [
                sys.executable,
                str(PLUGIN_DIR / "run_backend.py"),
                "--config",
                str(SETTINGS_PATH),
                "--status",
                str(STATUS_PATH),
                "run",
            ]
            decky.logger.info("Starting Forza DualSense backend")
            self.process = await asyncio.create_subprocess_exec(
                *command,
                cwd=str(PLUGIN_DIR),
                stdout=asyncio.subprocess.PIPE,
                stderr=asyncio.subprocess.STDOUT,
                start_new_session=True,
            )
            self.loop.create_task(self._log_backend_output(self.process))
            return True

    async def _log_backend_output(self, process: asyncio.subprocess.Process) -> None:
        if process.stdout is None:
            return
        while True:
            line = await process.stdout.readline()
            if not line:
                break
            decky.logger.info("[engine] %s", line.decode(errors="replace").rstrip())

    async def _stop_backend(self) -> None:
        async with self.process_lock:
            process = self.process
            self.process = None
            if process is None or process.returncode is not None:
                return

            decky.logger.info("Stopping Forza DualSense backend")
            try:
                os.killpg(process.pid, signal.SIGTERM)
            except ProcessLookupError:
                return

            try:
                await asyncio.wait_for(process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                try:
                    os.killpg(process.pid, signal.SIGKILL)
                except ProcessLookupError:
                    pass
                await process.wait()

    async def restart_backend(self) -> bool:
        await self._stop_backend()
        return await self._start_backend()

    async def get_status(self) -> dict[str, Any]:
        running = self.process is not None and self.process.returncode is None
        default = {
            "running": running,
            "enabled": True,
            "telemetry": "waiting",
            "controller": "disconnected",
            "controller_name": "",
            "controller_transport": "",
            "brake_effect": "clear",
            "throttle_effect": "clear",
            "speed_kmh": 0.0,
            "rpm": 0.0,
            "rpm_ratio": 0.0,
            "gear": 0,
        }
        try:
            if STATUS_PATH.exists():
                data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
                default.update(data)
        except (OSError, json.JSONDecodeError) as exc:
            decky.logger.warning("Could not read status: %s", exc)
        default["running"] = running
        return default

    async def get_settings(self) -> dict[str, Any]:
        await self._ensure_settings()
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))

    async def update_setting(self, key: str, value: Any) -> dict[str, Any]:
        if key not in ALLOWED_CONTROLS:
            raise ValueError(f"Unsupported setting: {key}")

        settings = await self.get_settings()
        if key == "enabled":
            settings[key] = bool(value)
        else:
            numeric = float(value)
            if not 0.0 <= numeric <= 2.0:
                raise ValueError(f"{key} must be between 0.0 and 2.0")
            settings[key] = numeric

        temporary = SETTINGS_PATH.with_suffix(".tmp")
        temporary.write_text(json.dumps(settings, indent=2) + "\n", encoding="utf-8")
        temporary.replace(SETTINGS_PATH)
        await self.restart_backend()
        return settings

    async def _main(self):
        self.loop = asyncio.get_event_loop()
        self.process_lock = asyncio.Lock()
        await self._ensure_settings()
        await self._start_backend()
        decky.logger.info("Forza DualSense Haptics loaded")

    async def _unload(self):
        await self._stop_backend()
        decky.logger.info("Forza DualSense Haptics unloaded")

    async def _uninstall(self):
        await self._stop_backend()
