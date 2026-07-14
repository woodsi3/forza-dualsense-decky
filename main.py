from __future__ import annotations

import asyncio
import json
from pathlib import Path
import time
from typing import Any

import decky


PLUGIN_DIR = Path(__file__).resolve().parent
DECKY_HOME = Path(getattr(decky, "DECKY_HOME", "/home/deck/homebrew"))
SETTINGS_DIR = Path(getattr(decky, "DECKY_SETTINGS_DIR", DECKY_HOME / "settings"))
RUNTIME_DIR = Path(
    getattr(decky, "DECKY_RUNTIME_DIR", DECKY_HOME / "data" / "forza-dualsense-haptics")
)
LOG_DIR = Path(
    getattr(decky, "DECKY_LOG_DIR", DECKY_HOME / "logs" / "forza-dualsense-haptics")
)

SETTINGS_PATH = SETTINGS_DIR / "forza-dualsense-settings.json"
PRESETS_PATH = SETTINGS_DIR / "forza-dualsense-presets.json"
CAR_PROFILES_PATH = SETTINGS_DIR / "forza-dualsense-car-profiles.json"
STATUS_PATH = RUNTIME_DIR / "forza-dualsense-status.json"
COMMAND_PATH = RUNTIME_DIR / "forza-dualsense-command.json"
ENGINE_LOG_PATH = LOG_DIR / "forza-dualsense-engine.log"
EXAMPLE_SETTINGS = PLUGIN_DIR / "settings.example.json"
ALLOWED_CONTROLS = {
    "enabled",
    "pedal_force_intensity",
    "abs_intensity",
    "gear_kick_intensity",
    "rev_limiter_intensity",
    "traction_intensity",
    "pedal_response_curve",
    "traction_response_curve",
    "traction_enabled",
    "traction_mild_slip",
    "traction_heavy_slip",
    "automatic_car_profiles",
}
PRESET_KEYS = [
    "pedal_force_intensity",
    "abs_intensity",
    "gear_kick_intensity",
    "rev_limiter_intensity",
    "traction_intensity",
    "pedal_response_curve",
    "traction_response_curve",
    "traction_enabled",
    "traction_mild_slip",
    "traction_heavy_slip",
]


class Plugin:
    process: asyncio.subprocess.Process | None = None
    process_lock: asyncio.Lock
    settings_lock: asyncio.Lock
    startup_task: asyncio.Task | None = None
    backend_error: str = ""
    last_auto_car: int = 0
    active_profile: str = "Global"

    async def _ensure_settings(self) -> None:
        SETTINGS_PATH.parent.mkdir(parents=True, exist_ok=True)
        STATUS_PATH.parent.mkdir(parents=True, exist_ok=True)

        defaults = json.loads(EXAMPLE_SETTINGS.read_text(encoding="utf-8"))

        # Migrate existing settings by adding newly introduced keys while
        # preserving every existing user value.
        if SETTINGS_PATH.exists():
            existing = json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))
            migrated = {**defaults, **existing}
            if migrated != existing:
                self._atomic_write(SETTINGS_PATH, migrated)
                decky.logger.info("Migrated settings schema with new defaults")
        else:
            self._atomic_write(SETTINGS_PATH, defaults)

        preset_defaults = {
            key: defaults[key]
            for key in PRESET_KEYS
        }

        if PRESETS_PATH.exists():
            presets = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
            migrated_presets = {}

            for name, preset in presets.items():
                migrated_preset = dict(preset_defaults)
                if isinstance(preset, dict):
                    migrated_preset.update(
                        {
                            key: value
                            for key, value in preset.items()
                            if key in PRESET_KEYS
                        }
                    )
                migrated_presets[name] = migrated_preset

            if migrated_presets != presets:
                self._atomic_write(PRESETS_PATH, migrated_presets)
                decky.logger.info("Migrated presets schema with new defaults")
        else:
            intensity_keys = {
                "pedal_force_intensity",
                "abs_intensity",
                "gear_kick_intensity",
                "rev_limiter_intensity",
                "traction_intensity",
            }

            presets = {}
            for name, scale in (
                ("Balanced", 1.0),
                ("Subtle", 0.65),
                ("Strong", 1.35),
            ):
                preset = dict(preset_defaults)
                for key in intensity_keys:
                    preset[key] = scale
                presets[name] = preset

            self._atomic_write(PRESETS_PATH, presets)

        if not CAR_PROFILES_PATH.exists():
            self._atomic_write(CAR_PROFILES_PATH, {})

    @staticmethod
    def _atomic_write(path: Path, data: Any) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        temporary = path.with_suffix(path.suffix + ".tmp")
        temporary.write_text(json.dumps(data, indent=2) + "\n", encoding="utf-8")
        temporary.replace(path)

    async def _start_backend(self) -> bool:
        async with self.process_lock:
            if self.process is not None and self.process.returncode is None:
                return True
            try:
                await self._ensure_settings()
                command = [
                    "/usr/bin/python3",
                    str(PLUGIN_DIR / "run_backend.py"),
                    "--config", str(SETTINGS_PATH),
                    "--status", str(STATUS_PATH),
                    "--command-file", str(COMMAND_PATH),
                    "run",
                ]
                ENGINE_LOG_PATH.parent.mkdir(parents=True, exist_ok=True)
                log_handle = open(ENGINE_LOG_PATH, "ab", buffering=0)
                self.process = await asyncio.create_subprocess_exec(
                    *command,
                    cwd=str(PLUGIN_DIR),
                    stdout=log_handle,
                    stderr=log_handle,
                )
                self.backend_error = ""
                self.loop.create_task(self._watch_backend(self.process))
                decky.logger.info("Forza DualSense backend started with PID %s", self.process.pid)
                return True
            except Exception as exc:
                self.process = None
                self.backend_error = f"{type(exc).__name__}: {exc}"
                decky.logger.exception("Could not start Forza DualSense backend")
                return False

    async def _startup_backend(self) -> None:
        await asyncio.sleep(0)
        await self._start_backend()

    async def _watch_backend(self, process: asyncio.subprocess.Process) -> None:
        return_code = await process.wait()
        if self.process is process:
            self.process = None
        if return_code != 0:
            self.backend_error = f"Engine exited with code {return_code}. Check {ENGINE_LOG_PATH}"
            decky.logger.error(self.backend_error)

    async def _stop_backend(self) -> None:
        async with self.process_lock:
            process = self.process
            self.process = None
            if process is None or process.returncode is not None:
                return
            decky.logger.info("Stopping exact backend child PID %s", process.pid)
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

    async def _apply_automatic_car_profile(self, status: dict[str, Any]) -> None:
        settings = await self.get_settings()
        car_ordinal = int(status.get("car_ordinal", 0) or 0)
        if not settings.get("automatic_car_profiles", False) or car_ordinal <= 0:
            self.active_profile = "Global"
            self.last_auto_car = car_ordinal
            return
        if car_ordinal == self.last_auto_car:
            return
        self.last_auto_car = car_ordinal
        profiles = await self.get_car_profiles()
        preset_name = profiles.get(str(car_ordinal))
        if not preset_name:
            self.active_profile = "Global"
            return
        presets = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
        preset = presets.get(preset_name)
        if not isinstance(preset, dict):
            self.active_profile = "Global"
            return
        settings.update(preset)
        self._atomic_write(SETTINGS_PATH, settings)
        self.active_profile = preset_name
        decky.logger.info("Auto-loaded preset %s for car %s", preset_name, car_ordinal)

    async def get_status(self) -> dict[str, Any]:
        running = self.process is not None and self.process.returncode is None
        default: dict[str, Any] = {
            "running": running,
            "enabled": True,
            "telemetry": "waiting",
            "controller": "disconnected",
            "controller_name": "",
            "controller_transport": "",
            "controller_path": "",
            "controller_serial": "",
            "controller_product_id": "",
            "controller_firmware": "Unavailable through hidraw",
            "controller_battery_percent": None,
            "controller_battery_status": "Unavailable",
            "brake_effect": "clear",
            "throttle_effect": "clear",
            "active_test": "",
            "settings_revision": 0,
            "speed_kmh": 0.0,
            "rpm": 0.0,
            "rpm_ratio": 0.0,
            "gear": 0,
            "backend_error": self.backend_error,
        }
        try:
            if STATUS_PATH.exists():
                default.update(json.loads(STATUS_PATH.read_text(encoding="utf-8")))
        except (OSError, json.JSONDecodeError) as exc:
            decky.logger.warning("Could not read status: %s", exc)
        default["running"] = running
        default["backend_error"] = self.backend_error
        try:
            await self._apply_automatic_car_profile(default)
        except Exception as exc:
            decky.logger.warning("Automatic car-profile selection failed: %s", exc)
        default["active_profile"] = self.active_profile
        return default

    async def get_settings(self) -> dict[str, Any]:
        await self._ensure_settings()
        return json.loads(SETTINGS_PATH.read_text(encoding="utf-8"))

    async def update_setting(self, update: dict[str, Any]) -> dict[str, Any]:
        if not isinstance(update, dict):
            raise TypeError("Settings update must be an object")
        key = update.get("key")
        value = update.get("value")
        if not isinstance(key, str) or key not in ALLOWED_CONTROLS:
            raise ValueError(f"Unsupported setting: {key}")
        async with self.settings_lock:
            settings = await self.get_settings()
            if key in {"enabled", "traction_enabled", "automatic_car_profiles"}:
                settings[key] = bool(value)
            elif key in {"pedal_response_curve", "traction_response_curve"}:
                if value not in {"linear", "progressive", "aggressive"}:
                    raise ValueError("Unsupported response curve")
                settings[key] = value
            else:
                numeric = float(value)
                if key.endswith("_intensity") and not 0.0 <= numeric <= 2.0:
                    raise ValueError(f"{key} must be between 0.0 and 2.0")
                settings[key] = numeric
            self._atomic_write(SETTINGS_PATH, settings)
            decky.logger.info("Persisted setting %s=%s", key, settings[key])
            return settings

    async def list_presets(self) -> list[str]:
        await self._ensure_settings()
        presets = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
        return sorted(presets.keys(), key=str.lower)

    async def create_preset(self) -> str:
        settings = await self.get_settings()
        presets = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
        index = 1
        while f"Preset {index}" in presets:
            index += 1
        name = f"Preset {index}"
        presets[name] = {key: settings[key] for key in PRESET_KEYS}
        self._atomic_write(PRESETS_PATH, presets)
        return name

    async def load_preset(self, name: str) -> dict[str, Any]:
        presets = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
        if name not in presets:
            raise ValueError(f"Preset not found: {name}")
        settings = await self.get_settings()
        settings.update(presets[name])
        self._atomic_write(SETTINGS_PATH, settings)
        return settings

    async def duplicate_preset(self, name: str) -> str:
        presets = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
        if name not in presets:
            raise ValueError(f"Preset not found: {name}")
        base = f"{name} Copy"
        candidate = base
        index = 2
        while candidate in presets:
            candidate = f"{base} {index}"
            index += 1
        presets[candidate] = dict(presets[name])
        self._atomic_write(PRESETS_PATH, presets)
        return candidate

    async def delete_preset(self, name: str) -> bool:
        presets = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
        if name not in presets:
            return False
        del presets[name]
        self._atomic_write(PRESETS_PATH, presets)
        return True

    async def get_car_profiles(self) -> dict[str, str]:
        await self._ensure_settings()
        return json.loads(CAR_PROFILES_PATH.read_text(encoding="utf-8"))

    async def assign_current_car_profile(self, request: dict[str, Any]) -> bool:
        car_ordinal = str(request.get("car_ordinal", "0"))
        preset = str(request.get("preset", ""))
        presets = json.loads(PRESETS_PATH.read_text(encoding="utf-8"))
        if not car_ordinal or car_ordinal == "0":
            raise ValueError("No current car detected")
        if preset not in presets:
            raise ValueError("Preset not found")
        profiles = await self.get_car_profiles()
        profiles[car_ordinal] = preset
        self._atomic_write(CAR_PROFILES_PATH, profiles)
        return True

    async def remove_current_car_profile(self, car_ordinal: int) -> bool:
        profiles = await self.get_car_profiles()
        profiles.pop(str(car_ordinal), None)
        self._atomic_write(CAR_PROFILES_PATH, profiles)
        return True

    async def test_effect(self, effect: str) -> bool:
        if effect not in {"pedal", "abs", "gear", "rev"}:
            raise ValueError(f"Unsupported test effect: {effect}")
        self._atomic_write(
            COMMAND_PATH,
            {"id": str(time.time_ns()), "type": "test_effect", "effect": effect},
        )
        return True

    async def _main(self):
        self.loop = asyncio.get_event_loop()
        self.process_lock = asyncio.Lock()
        self.settings_lock = asyncio.Lock()
        await self._ensure_settings()
        self.startup_task = self.loop.create_task(self._startup_backend())
        decky.logger.info("Forza DualSense Haptics v0.5.0 loaded")

    async def _unload(self):
        if self.startup_task is not None and not self.startup_task.done():
            self.startup_task.cancel()
            try:
                await self.startup_task
            except asyncio.CancelledError:
                pass
        await self._stop_backend()

    async def _uninstall(self):
        await self._stop_backend()
