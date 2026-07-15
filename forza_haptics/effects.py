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

        # State used by traction guidance. Slip trend helps the trigger react
        # while grip is deteriorating, before full wheelspin is established.
        self._previous_rear_slip = 0.0
        self._previous_slip_time = time.monotonic()

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
        now = time.monotonic()
        slip = state.rear_slip

        elapsed = max(
            0.001,
            min(0.25, now - self._previous_slip_time),
        )
        slip_rate = (slip - self._previous_rear_slip) / elapsed

        self._previous_rear_slip = slip
        self._previous_slip_time = now

        if (
            not self.settings.traction_enabled
            or state.throttle < self.settings.traction_min_throttle
            or state.speed_kmh < self.settings.traction_min_speed_kmh
        ):
            return "stable", 0.0

        throttle_span = max(
            1,
            255 - self.settings.traction_min_throttle,
        )
        throttle_demand = (
            state.throttle - self.settings.traction_min_throttle
        ) / throttle_span
        throttle_demand = max(0.0, min(1.0, throttle_demand))

        # Start guidance well before established wheelspin. This represents
        # the tyres approaching their available grip rather than merely
        # reporting traction loss after it has happened.
        onset_slip = self.settings.traction_mild_slip * 0.30

        slip_span = self.settings.traction_heavy_slip - onset_slip
        grip_usage = (slip - onset_slip) / max(slip_span, 0.001)
        grip_usage = max(0.0, min(1.0, grip_usage))

        # Positive slip rate means grip is deteriorating. Negative slip rate
        # never adds force, allowing the trigger to relax during recovery.
        rising_slip = max(0.0, slip_rate)
        trend = min(1.0, rising_slip / 1.25)

        curved_usage = self._curve(
            grip_usage,
            self.settings.traction_response_curve,
        )

        # Preserve the selected response curve, but ensure the early part of
        # the guidance remains perceptible.
        early_usage = grip_usage ** 0.55
        grip_component = max(curved_usage, early_usage)

        # Slip trend is most meaningful when the driver is demanding power.
        trend_component = trend * throttle_demand

        # Absolute grip usage remains dominant. The trend component advances
        # the force slightly when wheelspin is developing rapidly.
        severity = (
            grip_component * 0.78
            + trend_component * 0.22
        )

        # Do not generate guidance solely from telemetry noise at very low
        # grip usage. A meaningful slip level or trend must exist.
        if grip_usage < 0.015 and trend_component < 0.08:
            severity = 0.0

        severity = max(0.0, min(1.0, severity))

        if slip >= self.settings.traction_heavy_slip:
            traction_state = "heavy slip"
        elif slip >= self.settings.traction_mild_slip:
            traction_state = "mild slip"
        elif severity > 0.0:
            traction_state = "approaching limit"
        else:
            traction_state = "stable"

        return traction_state, severity

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
        time_constant = (
            0.055
            if target_extra > self._traction_extra_force
            else 0.18
        )
        smoothing = 1.0 - pow(
            2.718281828,
            -elapsed / time_constant,
        )

        desired_change = (
            target_extra - self._traction_extra_force
        ) * smoothing

        # Limit how quickly resistance may change between telemetry frames.
        # This is the main protection against smooth modulation becoming a
        # vibration-like sensation.
        maximum_rise = 240.0 * elapsed
        maximum_fall = 180.0 * elapsed

        if desired_change > 0.0:
            desired_change = min(desired_change, maximum_rise)
        else:
            desired_change = max(desired_change, -maximum_fall)

        self._traction_extra_force += desired_change

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
