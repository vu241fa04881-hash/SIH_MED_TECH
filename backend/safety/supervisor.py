"""MoveAssist Safety Supervisor (Highest Authority)
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import math
from enum import Enum
from typing import Dict, Any, List, Optional
from backend.config import DEFAULT_SAFETY


class SafetyMode(str, Enum):
    NORMAL_AAN = "NORMAL_AAN"
    PROTECTIVE_MODE = "PROTECTIVE_MODE"
    SAFE_FALLBACK = "SAFE_FALLBACK"
    CONTROLLED_SOFT_STOP = "CONTROLLED_SOFT_STOP"
    EMERGENCY_STOP = "EMERGENCY_STOP"


class SafetySupervisor:
    """Highest Authority in the exoskeleton control hierarchy.

    
    Enforces non-negotiable hard safety constraints:
    1. Latching Emergency Stop (E-Stop) instant torque cutoff to 0.0 Nm.
    2. Controlled Soft E-Stop (Anti-Fall Deceleration): When high muscle fatigue
       or imminent collapse is detected, gently decelerates movement over 1-2 minutes
       with active anti-collapse knee support torque to prevent the patient from falling.
    3. Hard torque ceiling clamping (|tau| <= 35.0 Nm).
    4. Slew-rate limiting (|d(tau)/dt| <= 120.0 Nm/s) to eliminate shock loads.
    5. Anatomical ROM boundary enforcement (0.0 deg <= theta <= 115.0 deg).
    6. Sensor fault & heartbeat detection triggering Safe Fallback Mode.
    """

    def __init__(self, dt: float = 0.01):
        self.dt = dt
        self.mode = SafetyMode.NORMAL_AAN
        self.e_stop_latched = False
        self.prev_safe_torque = 0.0

        # Anti-Collapse Controlled Soft Stop State (1 to 2 minutes)
        self.soft_stop_active: bool = False
        self.soft_stop_elapsed_s: float = 0.0
        self.soft_stop_duration_s: float = getattr(DEFAULT_SAFETY, "controlled_soft_stop_default_duration_s", 90.0)
        self.soft_stop_reason: str = ""
        self.anti_collapse_torque: float = getattr(DEFAULT_SAFETY, "anti_collapse_support_torque_nm", 18.0)
        self.fall_seriousness: str = "NORMAL"

        # Hard boundaries
        self.max_torque = DEFAULT_SAFETY.max_torque_nm
        self.max_slew_rate = DEFAULT_SAFETY.max_slew_rate_nm_per_s
        self.min_rom = DEFAULT_SAFETY.min_rom_deg
        self.max_rom = DEFAULT_SAFETY.max_rom_deg
        self.soft_rom_margin = DEFAULT_SAFETY.soft_rom_margin_deg

        # Active safety intervention alerts
        self.active_alerts: List[str] = []
        self.fault_counter = 0

    def trigger_estop(self, reason: str = "MANUAL_ESTOP_PRESSED") -> None:
        """Latches Hard Emergency Stop immediately (instant torque cutoff)."""
        self.e_stop_latched = True
        self.mode = SafetyMode.EMERGENCY_STOP
        self.soft_stop_active = False
        self.prev_safe_torque = 0.0
        if reason not in self.active_alerts:
            self.active_alerts.append(f"CRITICAL: {reason}")

    def trigger_controlled_soft_stop(self, duration_s: float = 90.0,
                                     reason: str = "HIGH_MUSCLE_FATIGUE_FALL_RISK",
                                     seriousness: str = "NORMAL") -> None:
        """Initiates Controlled Soft E-Stop:

        Progressively decelerates movement over 30s to 2 minutes (default 90s)
        while maintaining anti-collapse upright supportive torque so the exhausted
        patient does not fall.
        """
        # Hard E-stop takes precedence
        if self.e_stop_latched:
            return

        self.soft_stop_active = True
        self.soft_stop_elapsed_s = 0.0
        self.soft_stop_duration_s = max(10.0, min(180.0, float(duration_s)))
        self.soft_stop_reason = reason
        self.fall_seriousness = seriousness
        self.mode = SafetyMode.CONTROLLED_SOFT_STOP

        msg = f"CRITICAL: {reason} — Controlled soft stop initiated (decelerating over {int(self.soft_stop_duration_s)}s)"
        if msg not in self.active_alerts:
            self.active_alerts = [a for a in self.active_alerts if not a.startswith("CRITICAL")]
            self.active_alerts.append(msg)

    def update_soft_stop_duration(self, new_duration_s: float,
                                  reason: str = "URGENCY_ESCALATION",
                                  seriousness: str = "") -> None:
        """
        Dynamically updates the active soft stop timer to a shorter duration (e.g. 30s)
        when patient fatigue worsens or fall risk seriousness escalates to imminent collapse.
        """
        if not self.soft_stop_active or self.e_stop_latched:
            return

        new_dur = max(10.0, min(180.0, float(new_duration_s)))
        # Only tighten/accelerate if more urgent than currently scheduled duration
        if new_dur < self.soft_stop_duration_s:
            old_progress = min(1.0, self.soft_stop_elapsed_s / max(0.001, self.soft_stop_duration_s))
            self.soft_stop_duration_s = new_dur
            # Scale elapsed time smoothly so progress advances gracefully without discontinuity
            self.soft_stop_elapsed_s = old_progress * new_dur
            self.soft_stop_reason = f"{self.soft_stop_reason} -> {reason}"
            if seriousness:
                self.fall_seriousness = seriousness
            rem_s = max(0.0, self.soft_stop_duration_s - self.soft_stop_elapsed_s)
            msg = f"CRITICAL: Emergency deceleration dynamically accelerated to {int(self.soft_stop_duration_s)}s ({int(rem_s)}s remaining) — {reason}"
            self.active_alerts = [a for a in self.active_alerts if "dynamically accelerated" not in a and not a.startswith("CRITICAL: URGENCY")]
            self.active_alerts.append(msg)

    def reset_soft_stop(self) -> None:
        """Restores normal adaptive AAN from Controlled Soft Stop."""
        self.soft_stop_active = False
        self.soft_stop_elapsed_s = 0.0
        self.fall_seriousness = "NORMAL"
        self.mode = SafetyMode.NORMAL_AAN
        self.active_alerts = [a for a in self.active_alerts if "soft stop" not in a.lower() and "accelerated" not in a.lower()]

    def reset_estop(self) -> bool:
        """Resets the latched E-stop and soft stop only if no critical sensor faults remain."""
        if self.fault_counter > 0:
            return False
        self.e_stop_latched = False
        self.soft_stop_active = False
        self.soft_stop_elapsed_s = 0.0
        self.mode = SafetyMode.NORMAL_AAN
        self.prev_safe_torque = 0.0
        self.active_alerts = [a for a in self.active_alerts if not a.startswith("CRITICAL")]
        return True

    def process(self, raw_cmd_torque: float, knee_angle_deg: float,
                knee_vel_deg_s: float, sensors_healthy: bool,
                spasm_detected: bool = False) -> Dict[str, Any]:
        """Filters commanded torque through the multi-tier safety architecture."""
        alerts: List[str] = []

        # 1. Check Latching Emergency Stop
        if self.e_stop_latched:
            self.mode = SafetyMode.EMERGENCY_STOP
            self.prev_safe_torque = 0.0
            return {
                "safe_torque_nm": 0.0,
                "mode": self.mode.value,
                "e_stop_latched": True,
                "alerts": ["CRITICAL: EMERGENCY_STOP_ENGAGED"]
            }

        # 2. Check Sensor Integrity
        if not sensors_healthy:
            self.fault_counter += 1
            self.mode = SafetyMode.SAFE_FALLBACK
            alerts.append("WARN: Sensor anomaly detected - SAFE FALLBACK engaged")
            damping = -0.15 * math.radians(knee_vel_deg_s)
            fallback_target = max(-8.0, min(8.0, damping))
            clamped_torque = self._apply_slew_rate(fallback_target)
            self.prev_safe_torque = clamped_torque
            return {
                "safe_torque_nm": round(clamped_torque, 3),
                "mode": self.mode.value,
                "e_stop_latched": False,
                "alerts": alerts,
                "controlled_soft_stop": {"active": False}
            }
        else:
            self.fault_counter = 0

        # 3. Controlled Soft E-Stop (Anti-Fall Progressive Deceleration over 1 to 2 min)
        if self.soft_stop_active:
            self.mode = SafetyMode.CONTROLLED_SOFT_STOP
            self.soft_stop_elapsed_s += self.dt
            p = min(1.0, self.soft_stop_elapsed_s / self.soft_stop_duration_s)
            rem_s = max(0.0, self.soft_stop_duration_s - self.soft_stop_elapsed_s)

            # Smooth s-curve blending towards anti-collapse extension holding torque
            blend = 0.5 * (1.0 - math.cos(p * math.pi))  # Smooth cosine ease-in-out
            anti_fall_target = (1.0 - blend) * raw_cmd_torque + blend * self.anti_collapse_torque
            # Progressive viscous damping to gently settle joint oscillations
            damping = -(0.25 + 0.35 * blend) * math.radians(knee_vel_deg_s)
            target_with_damping = anti_fall_target + damping

            alerts.append(f"CRITICAL: CONTROLLED SOFT E-STOP — Anti-fall deceleration {round(p * 100)}% ({int(rem_s)}s remaining)")
            raw_cmd_torque = target_with_damping
        elif spasm_detected:
            self.mode = SafetyMode.PROTECTIVE_MODE
            alerts.append("WARN: High involuntary tremor/spasm detected - PROTECTIVE MODE active")
            protective_target = raw_cmd_torque * 0.35 - (0.40 * math.radians(knee_vel_deg_s))
            raw_cmd_torque = protective_target
        elif self.mode != SafetyMode.EMERGENCY_STOP:
            self.mode = SafetyMode.NORMAL_AAN

        # 4. Anatomical ROM Enforcement & Soft Boundary Pushback
        rom_limited_torque = raw_cmd_torque

        # Extension limit check (0.0 deg)
        if knee_angle_deg <= self.min_rom:
            if rom_limited_torque > 0:  # Trying to extend past hyperextension boundary
                rom_limited_torque = 0.0
                alerts.append("ALERT: Hyperextension limit reached (0 deg) - Extension torque stopped")
        elif knee_angle_deg < (self.min_rom + self.soft_rom_margin):
            # Soft buffer zone: apply resistive pushback away from boundary
            penetration = (self.min_rom + self.soft_rom_margin - knee_angle_deg) / self.soft_rom_margin
            rom_limited_torque -= (8.0 * penetration)

        # Flexion limit check (115.0 deg)
        if knee_angle_deg >= self.max_rom:
            if rom_limited_torque < 0:  # Trying to flex deeper past boundary
                rom_limited_torque = 0.0
                alerts.append("ALERT: Hyperflexion limit reached (115 deg) - Flexion torque stopped")
        elif knee_angle_deg > (self.max_rom - self.soft_rom_margin):
            penetration = (knee_angle_deg - (self.max_rom - self.soft_rom_margin)) / self.soft_rom_margin
            rom_limited_torque += (8.0 * penetration)

        # 5. Hard Torque Ceiling Clamping (|tau| <= 35.0 Nm)
        if rom_limited_torque > self.max_torque:
            alerts.append(f"LIMIT: Torque ceiling reached (+{self.max_torque} Nm)")
            ceiling_clamped = self.max_torque
        elif rom_limited_torque < -self.max_torque:
            alerts.append(f"LIMIT: Torque floor reached (-{self.max_torque} Nm)")
            ceiling_clamped = -self.max_torque
        else:
            ceiling_clamped = rom_limited_torque

        # 6. Slew-Rate Limiting (|d(tau)/dt| <= 120.0 Nm/s)
        final_safe_torque = self._apply_slew_rate(ceiling_clamped)
        if abs((final_safe_torque - self.prev_safe_torque) / self.dt) >= (self.max_slew_rate - 0.1):
            alerts.append(f"LIMIT: Slew rate limit reached ({self.max_slew_rate} Nm/s)")

        self.prev_safe_torque = final_safe_torque
        self.active_alerts = alerts

        p_soft = min(1.0, self.soft_stop_elapsed_s / self.soft_stop_duration_s) if self.soft_stop_active else 0.0
        rem_soft = max(0.0, self.soft_stop_duration_s - self.soft_stop_elapsed_s) if self.soft_stop_active else 0.0

        return {
            "safe_torque_nm": round(final_safe_torque, 3),
            "mode": self.mode.value,
            "e_stop_latched": False,
            "alerts": alerts,
            "controlled_soft_stop": {
                "active": self.soft_stop_active,
                "progress_pct": round(p_soft * 100.0, 1),
                "elapsed_s": round(self.soft_stop_elapsed_s, 1),
                "duration_s": round(self.soft_stop_duration_s, 1),
                "remaining_s": round(rem_soft, 1),
                "velocity_scale": round(max(0.0, 1.0 - (p_soft ** 1.5)), 3),
                "reason": self.soft_stop_reason,
                "fall_seriousness": getattr(self, "fall_seriousness", "NORMAL")
            }
        }

    def _apply_slew_rate(self, target_torque: float) -> float:
        """Limits rate of torque change to max_slew_rate."""
        max_delta = self.max_slew_rate * self.dt
        delta = target_torque - self.prev_safe_torque

        if delta > max_delta:
            return self.prev_safe_torque + max_delta
        elif delta < -max_delta:
            return self.prev_safe_torque - max_delta
        else:
            return target_torque
