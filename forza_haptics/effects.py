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
    traction_state: str = "stable"
    last_gear: int = 0
    gear_kick_until: float = 0.0
    rev_limiter_active: bool = False

class EffectEngine:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.status = EffectStatus()

        # Smoothed traction contribution applied to R2.
        # This prevents noisy wheel-slip telemetry from making the trigger
        # chatter or pulse.
        self._traction_extra_force = 0.0
        self._traction_update_time = time.monotonic()

    @staticmethod
    def _scale(value: float, intensity: float) -> int:
        return max(0, min(255, int(round(value * intensity))))

    @staticmethod
    def _curve(value: float, curve: str) -> float:
        value = max(0.0, min(1.0, value))
        if curve == "linear":
            return value
        if curve == "aggressive":
            return value ** 0.65
        return value ** 1.7

    def _pedal_force(self, pedal: int, base: int, maximum: int) -> int:
        ratio = self._curve(pedal / 255.0, self.settings.pedal_response_curve)
        raw = base + (maximum - base) * ratio
        return self._scale(raw, self.settings.pedal_force_intensity)

    def _traction(self, state: VehicleState) -> tuple[str, float]:
        if (
            not self.settings.traction_enabled
            or state.throttle < self.settings.traction_min_throttle
            or state.speed_kmh < self.settings.traction_min_speed_kmh
        ):
            return "stable", 0.0
        slip = state.rear_slip
        if slip < self.settings.traction_mild_slip:
            return "stable", 0.0
        span = self.settings.traction_heavy_slip - self.settings.traction_mild_slip
        severity = (slip - self.settings.traction_mild_slip) / max(span, 0.001)
        severity = self._curve(severity, self.settings.traction_response_curve)
        return ("heavy slip" if slip >= self.settings.traction_heavy_slip else "mild slip"), min(1.0, severity)

    def compute(self, state: VehicleState) -> tuple[TriggerEffect, TriggerEffect]:
        now = time.monotonic()
        if not self.settings.enabled or not state.is_racing:
            self.status.brake_mode = "clear"
            self.status.throttle_mode = "clear"
            self.status.traction_state = "stable"
            self.status.last_gear = state.gear
            return clear_effect(), clear_effect()

        brake_force = self._pedal_force(state.brake, self.settings.brake_base_force, self.settings.brake_max_force)
        throttle_force = self._pedal_force(state.throttle, self.settings.throttle_base_force, self.settings.throttle_max_force)
        brake_effect = resistance(0, brake_force)
        throttle_effect = resistance(0, throttle_force)
        self.status.brake_mode = "pedal resistance"
        self.status.throttle_mode = "pedal resistance"

        abs_active = (
            state.brake >= self.settings.abs_min_brake
            and state.speed_kmh >= self.settings.abs_min_speed_kmh
            and state.front_slip >= self.settings.abs_slip_threshold
        )
        if abs_active:
            brake_effect = vibration(35, self._scale(self.settings.abs_amplitude, self.settings.abs_intensity), self.settings.abs_frequency)
            self.status.brake_mode = "ABS vibration"

        if self.status.last_gear not in (0, 10) and state.gear not in (0, 10) and state.gear != self.status.last_gear:
            self.status.gear_kick_until = now + self.settings.gear_kick_duration_ms / 1000.0

        if self.status.rev_limiter_active:
            if state.rpm_ratio < self.settings.rev_limiter_release_ratio or state.throttle <= self.settings.rev_limiter_min_throttle:
                self.status.rev_limiter_active = False
        elif state.rpm_ratio >= self.settings.rev_limiter_ratio and state.throttle > self.settings.rev_limiter_min_throttle:
            self.status.rev_limiter_active = True

        traction_state, severity = self._traction(state)
        self.status.traction_state = traction_state

        # Traction feedback continuously modifies pedal resistance.
        # It never becomes a vibration effect; gear kick and rev limiter
        # remain the only event-style R2 pulses.
        target_extra = float(
            self._scale(
                self.settings.traction_max_extra_force * severity,
                self.settings.traction_intensity,
            )
        )

        update_time = time.monotonic()
        elapsed = max(0.0, min(0.25, update_time - self._traction_update_time))
        self._traction_update_time = update_time

        # Rise reasonably quickly when slip begins, then release more gently
        # as traction returns. The exponential form remains consistent if
        # the telemetry packet rate changes.
        time_constant = 0.10 if target_extra > self._traction_extra_force else 0.22
        smoothing = 1.0 - pow(2.718281828, -elapsed / time_constant)

        self._traction_extra_force += (
            target_extra - self._traction_extra_force
        ) * smoothing

        smoothed_extra = int(round(self._traction_extra_force))

        if smoothed_extra > 0:
            throttle_effect = resistance(
                0,
                min(255, throttle_force + smoothed_extra),
            )
            self.status.throttle_mode = f"traction {traction_state}"

        # Event effects override dynamic pedal/traction feedback briefly.
        if now < self.status.gear_kick_until:
            throttle_effect = vibration(20, self._scale(self.settings.gear_kick_amplitude, self.settings.gear_kick_intensity), self.settings.gear_kick_frequency)
            self.status.throttle_mode = "gear kick"
        elif self.status.rev_limiter_active:
            throttle_effect = vibration(25, self._scale(self.settings.rev_limiter_amplitude, self.settings.rev_limiter_intensity), self.settings.rev_limiter_frequency)
            self.status.throttle_mode = "rev limiter"

        self.status.last_gear = state.gear
        return brake_effect, throttle_effect
