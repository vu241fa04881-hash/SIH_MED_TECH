"""User Contribution Estimator & Muscle Fatigue Accumulator
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import math
from typing import Dict, Any


class UserModel:
    """Estimates the voluntary torque contributed by the human user:

    tau_user_estimated.
    
    Models patient active voluntary strength capacity, neuromuscular fatigue
    accumulation, and sudden motor spasms or tremors.
    Designated as a model estimate, not direct biological measurement.
    """

    def __init__(self, base_strength: float = 0.35):
        # Patient intrinsic strength capacity: 0.0 (paralyzed/flaccid) to 1.0 (healthy active)
        self.base_strength = max(0.05, min(1.0, float(base_strength)))
        self.effective_strength = self.base_strength
        
        # Muscle Fatigue index: 0.0 (fresh) to 1.0 (exhausted)
        self.fatigue_index = 0.0
        self.fatigue_accumulation_rate = 0.008   # Fatigue per second of high-effort flexion
        self.fatigue_recovery_rate = 0.004       # Passive recovery per second of low effort

        # Spasm / tremor injection state for deterioration demonstration
        self.spasm_active = False
        self.spasm_intensity = 0.0
        self.spasm_timer = 0.0

        # Estimated outputs
        self.tau_user_estimated = 0.0
        self.emg_envelope = 0.0

    def set_base_strength(self, strength: float) -> None:
        self.base_strength = max(0.05, min(1.0, float(strength)))

    def set_fatigue(self, fatigue: float) -> None:
        self.fatigue_index = max(0.0, min(1.0, float(fatigue)))

    def trigger_spasm(self, active: bool = True, intensity: float = 1.0) -> None:
        self.spasm_active = active
        self.spasm_intensity = intensity
        self.spasm_timer = 0.0

    def step(self, dt: float, tau_required: float, knee_angle_deg: float,
             gait_phase: str, is_active_swing: bool) -> Dict[str, float]:
        """Calculates instantaneous voluntary user torque contribution."""
        # 1. Update fatigue state
        if self.base_strength > 0.4 and abs(tau_required) > 5.0:
            # Active effort accumulates fatigue
            effort_factor = (abs(tau_required) / 25.0) * self.base_strength
            self.fatigue_index = min(1.0, self.fatigue_index + self.fatigue_accumulation_rate * effort_factor * dt)
        else:
            # Low effort allows gradual recovery
            self.fatigue_index = max(0.0, self.fatigue_index - self.fatigue_recovery_rate * dt)

        # 2. Effective strength degraded by fatigue
        fatigue_degradation = 1.0 - (0.65 * self.fatigue_index)
        self.effective_strength = max(0.05, self.base_strength * fatigue_degradation)

        # 3. Base voluntary torque estimate:
        # Patient supplies a fraction of required torque based on effective strength
        nominal_user_torque = tau_required * self.effective_strength

        # 4. Spasm / Tremor disturbance modeling (if active)
        spasm_torque = 0.0
        if self.spasm_active:
            self.spasm_timer += dt
            # Rapid erratic oscillations (12-16 Hz tremor + sudden clonic jerk)
            oscillation = math.sin(2.0 * math.pi * 14.0 * self.spasm_timer)
            clonic_jerk = 18.0 * math.sin(2.0 * math.pi * 3.5 * self.spasm_timer)
            spasm_torque = self.spasm_intensity * (oscillation * 8.0 + clonic_jerk)

        self.tau_user_estimated = nominal_user_torque + spasm_torque

        # 5. Simulated sEMG Envelope (correlated with voluntary activation + tremor)
        voluntary_drive = min(1.0, abs(self.tau_user_estimated) / 25.0)
        self.emg_envelope = min(1.0, voluntary_drive * 0.8 + (0.3 if self.spasm_active else 0.05))

        # 6. High Muscle Fatigue & Imminent Fall Risk Detection
        # When fatigue exceeds 85% or effective voluntary capacity collapses under load,
        # the patient experiences severe knee buckling risk (imminent fall).
        # Seriousness determines how rapidly the emergency deceleration must occur:
        # - Acute Immediate Fall (fatigue >= 95% or acute voluntary collapse): 30s Rapid Anti-Buckle Stop
        # - High Fall Risk (fatigue >= 90%): 60s Accelerated Stop
        # - Elevated Fall Risk (fatigue >= 85%): 90s Gradual Stop
        is_acute = (self.fatigue_index >= 0.95) or (self.fatigue_index >= 0.90 and self.effective_strength < 0.05)
        is_high = (self.fatigue_index >= 0.90) or (self.fatigue_index >= 0.85 and self.effective_strength < 0.08)
        is_elevated = (self.fatigue_index >= 0.85) or (self.fatigue_index >= 0.75 and self.effective_strength < 0.08)

        self.imminent_fall_risk = is_elevated or is_high or is_acute
        self.fall_risk_severity = max(0.0, min(1.0, (self.fatigue_index - 0.70) / 0.30)) if self.fatigue_index >= 0.70 else 0.0

        if is_acute:
            self.fall_seriousness = "ACUTE_IMMEDIATE_FALL"
            self.recommended_stop_duration_s = 30.0
        elif is_high:
            self.fall_seriousness = "HIGH"
            self.recommended_stop_duration_s = 60.0
        elif is_elevated:
            self.fall_seriousness = "ELEVATED"
            self.recommended_stop_duration_s = 90.0
        else:
            self.fall_seriousness = "NORMAL"
            self.recommended_stop_duration_s = 90.0

        return {
            "tau_user_estimated": self.tau_user_estimated,
            "base_strength": self.base_strength,
            "effective_strength": self.effective_strength,
            "fatigue_index": self.fatigue_index,
            "emg_envelope": self.emg_envelope,
            "spasm_active": self.spasm_active,
            "imminent_fall_risk": self.imminent_fall_risk,
            "fall_risk_severity": round(self.fall_risk_severity, 2),
            "fall_seriousness": self.fall_seriousness,
            "recommended_stop_duration_s": self.recommended_stop_duration_s
        }
