from __future__ import annotations

import asyncio
import json
import os
from pathlib import Path
from typing import Any

import decky


PLUGIN_DIR = Path(__file__).resolve().parent

# Compatibility across Decky Loader releases.
DECKY_HOME = Path(getattr(decky, "DECKY_HOME", "/home/deck/homebrew"))
SETTINGS_DIR = Path(getattr(decky, "DECKY_SETTINGS_DIR", DECKY_HOME / "settings"))
RUNTIME_DIR = Path(
    getattr(
        decky,
        "DECKY_RUNTIME_DIR",
        DECKY_HOME / "data" / "forza-dualsense-haptics",
    )
)
LOG_DIR = Path(
    getattr(
        decky,
        "DECKY_LOG_DIR",
        DECKY_HOME / "logs" / "forza-dualsense-haptics",
    )
)

SETTINGS_PATH = SETTINGS_DIR / "forza-dualsense-settings.json"
STATUS_PATH = RUNTIME_DIR / "forza-dualsense-status.json"
ENGINE_LOG_PATH = LOG_DIR / "forza-dualsense-engine.log"
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
    startup_task: asyncio.Task | None = None
    backend_error: str = ""

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

            try:
                await self._ensure_settings()
                command = [
                    "/usr/bin/python3",
                    str(PLUGIN_DIR / "run_backend.py"),
                    "--config",
                    str(SETTINGS_PATH),
                    "--status",
                    str(STATUS_PATH),
                    "run",
                ]
                ENGINE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                log_handle = open(ENGINE_LOG_PATH, "ab", buffering=0)

                decky.logger.info("Starting Forza DualSense backend: %s", command)
                self.process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=str(PLUGIN_DIR),
                    stdout=log_handle,
                    stderr=log_handle,
                )
                self.backend_error = ""
                decky.logger.info(
                    "Forza DualSense backend started with PID %s",
                    self.process.pid,
                )
                self.loop.create_task(self._watch_backend(self.process))
                return True
            except Exception as exc:
                self.process = None
                self.backend_error = f"{type(exc).__name__}: {exc}"
                decky.logger.exception("Could not start Forza DualSense backend")
                return False

    async def _startup_backend(self) -> None:
        # Runs after _main has returned, allowing Decky RPC calls to become
        # available even if process startup fails or takes longer than expected.
        await asyncio.sleep(0)
        await self._start_backend()

    async def _watch_backend(
        self,
        process: asyncio.subprocess.Process,
    ) -> None:
        return_code = await process.wait()
        if self.process is process:
            self.process = None
        if return_code != 0:
            self.backend_error = (
                f"Engine exited with code {return_code}. "
                f"Check {ENGINE_LOG_PATH}"
            )
            decky.logger.error(self.backend_error)
        else:
            decky.logger.info("Forza DualSense backend exited cleanly")

    async def _stop_backend(self) -> None:
        async with self.process_lock:
            process = self.process
            self.process = None
            if process is None or process.returncode is not None:
                return

            decky.logger.info(
                "Stopping Forza DualSense backend PID %s",
                process.pid,
            )

            # Only signal the exact child process. Never signal a process group:
            # on some SteamOS/Decky builds that can include the game-mode session.
            try:
                process.terminate()
            except ProcessLookupError:
                return

            try:
                await asyncio.wait_for(process.wait(), timeout=3.0)
            except asyncio.TimeoutError:
                try:
                    process.kill()
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
            "backend_error": self.backend_error,
        }
        try:
            if STATUS_PATH.exists():
                data = json.loads(STATUS_PATH.read_text(encoding="utf-8"))
                default.update(data)
        except (OSError, json.JSONDecodeError) as exc:
            decky.logger.warning("Could not read status: %s", exc)
        default["running"] = running
        default["backend_error"] = self.backend_error
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
        self.startup_task = self.loop.create_task(self._startup_backend())
        decky.logger.info(
            "Forza DualSense Haptics RPC backend loaded; engine startup scheduled"
        )

    async def _unload(self):
        if self.startup_task is not None and not self.startup_task.done():
            self.startup_task.cancel()
            try:
                await self.startup_task
            except asyncio.CancelledError:
                pass
        await self._stop_backend()
        decky.logger.info("Forza DualSense Haptics unloaded")

    async def _uninstall(self):
        await self._stop_backend()
