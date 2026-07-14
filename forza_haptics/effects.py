from __future__ import annotations

from dataclasses import dataclass
import time

from .config import Settings
from .telemetry import VehicleState
from .triggers import TriggerEffect, clear_effect, resistance, vibration


@dataclass
class EffectStatus:
    brake_mode: str = "clear"
    throttle_mode: str = "clear"
    last_gear: int = 0
    gear_kick_until: float = 0.0
    rev_limiter_active: bool = False


class EffectEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.status = EffectStatus()

    @staticmethod
    def _scale(value: float, intensity: float) -> int:
        return max(0, min(255, int(round(value * intensity))))

    @staticmethod
    def _max_abs(values: tuple[float, float, float, float]) -> float:
        return max(abs(value) for value in values)

    def _pedal_force(self, pedal: int, base: int, maximum: int) -> int:
        ratio = max(0.0, min(1.0, pedal / 255.0))
        curved = ratio ** 1.7
        raw = base + (maximum - base) * curved
        return self._scale(raw, self.settings.pedal_force_intensity)

    def compute(self, state: VehicleState) -> tuple[TriggerEffect, TriggerEffect]:
        now = time.monotonic()

        if not self.settings.enabled or not state.is_racing:
            self.status.brake_mode = "clear"
            self.status.throttle_mode = "clear"
            self.status.last_gear = state.gear
            return clear_effect(), clear_effect()

        brake_effect = resistance(
            0,
            self._pedal_force(
                state.brake,
                self.settings.brake_base_force,
                self.settings.brake_max_force,
            ),
        )
        throttle_effect = resistance(
            0,
            self._pedal_force(
                state.throttle,
                self.settings.throttle_base_force,
                self.settings.throttle_max_force,
            ),
        )
        self.status.brake_mode = "pedal resistance"
        self.status.throttle_mode = "pedal resistance"

        front_slip = max(
            self._max_abs((state.tire_slip_ratio[0], state.tire_slip_ratio[1], 0.0, 0.0)),
            self._max_abs((state.tire_combined_slip[0], state.tire_combined_slip[1], 0.0, 0.0)),
        )
        abs_active = (
            state.brake >= self.settings.abs_min_brake
            and state.speed_kmh >= self.settings.abs_min_speed_kmh
            and front_slip >= self.settings.abs_slip_threshold
        )
        if abs_active:
            brake_effect = vibration(
                position=35,
                amplitude=self._scale(
                    self.settings.abs_amplitude,
                    self.settings.abs_intensity,
                ),
                frequency=self.settings.abs_frequency,
            )
            self.status.brake_mode = "ABS vibration"

        if (
            self.status.last_gear not in (0, 10)
            and state.gear not in (0, 10)
            and state.gear != self.status.last_gear
        ):
            self.status.gear_kick_until = (
                now + self.settings.gear_kick_duration_ms / 1000.0
            )

        # Latch near redline and release lower to avoid rapid chatter.
        if self.status.rev_limiter_active:
            if (
                state.rpm_ratio < self.settings.rev_limiter_release_ratio
                or state.throttle <= self.settings.rev_limiter_min_throttle
            ):
                self.status.rev_limiter_active = False
        elif (
            state.rpm_ratio >= self.settings.rev_limiter_ratio
            and state.throttle > self.settings.rev_limiter_min_throttle
        ):
            self.status.rev_limiter_active = True

        if now < self.status.gear_kick_until:
            throttle_effect = vibration(
                position=20,
                amplitude=self._scale(
                    self.settings.gear_kick_amplitude,
                    self.settings.gear_kick_intensity,
                ),
                frequency=self.settings.gear_kick_frequency,
            )
            self.status.throttle_mode = "gear kick"
        elif self.status.rev_limiter_active:
            throttle_effect = vibration(
                position=25,
                amplitude=self._scale(
                    self.settings.rev_limiter_amplitude,
                    self.settings.rev_limiter_intensity,
                ),
                frequency=self.settings.rev_limiter_frequency,
            )
            self.status.throttle_mode = "rev limiter"

        self.status.last_gear = state.gear
        return brake_effect, throttle_effect
