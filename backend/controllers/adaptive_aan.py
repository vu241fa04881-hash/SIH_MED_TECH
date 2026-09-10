"""Two-Speed Adaptive Assist-As-Needed (AAN) Controller
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import math
from typing import Dict, Any, List
from backend.config import DEFAULT_AAN


class AdaptiveAANController:
    """Implements two-speed Assist-As-Needed (AAN) control:

    
    1. Fast Loop (100 Hz):
       - Computes instantaneous command: tau_cmd = K_aan * tau_deficit - B_virt * omega
       - Maintains smooth impedance interaction.
       
    2. Slow Loop (1-2 Hz):
       - Multi-cycle performance monitoring.
       - User contribution UP => Assistance Gain DOWN (stimulates neuroplasticity).
       - User contribution DOWN / Fatigue UP => Assistance Gain UP (prevents gait collapse).
    """

    def __init__(self, base_gain: float = DEFAULT_AAN.base_aan_gain):
        self.k_aan = max(DEFAULT_AAN.min_aan_gain, min(DEFAULT_AAN.max_aan_gain, base_gain))
        self.k_min = DEFAULT_AAN.min_aan_gain
        self.k_max = DEFAULT_AAN.max_aan_gain
        self.adaptation_rate = DEFAULT_AAN.adaptation_rate
        self.virtual_damping = 0.12  # Nm / (rad/s)

        # Performance history buffers for slow loop window
        self.history_user_torque: List[float] = []
        self.history_req_torque: List[float] = []
        self.history_deficit: List[float] = []
        self.window_size = 100  # 1 second at 100 Hz

        # Controller outputs
        self.tau_cmd = 0.0
        self.assistance_percent = 50.0
        self.user_percent = 50.0

        # Slow loop metrics
        self.avg_user_power = 0.0
        self.recent_participation_ratio = 0.5

    def reset(self) -> None:
        self.k_aan = DEFAULT_AAN.base_aan_gain
        self.history_user_torque.clear()
        self.history_req_torque.clear()
        self.history_deficit.clear()
        self.tau_cmd = 0.0

    def fast_loop_step(self, tau_deficit: float, omega_deg_s: float,
                       tau_user: float, tau_req: float) -> Dict[str, float]:
        """Executes the 100 Hz fast inner loop."""
        # Record history for slow loop
        self.history_user_torque.append(abs(tau_user))
        self.history_req_torque.append(abs(tau_req))
        self.history_deficit.append(abs(tau_deficit))
        if len(self.history_user_torque) > self.window_size:
            self.history_user_torque.pop(0)
            self.history_req_torque.pop(0)
            self.history_deficit.pop(0)

        # Impedance damping term
        omega_rad_s = math.radians(omega_deg_s)
        damping_torque = self.virtual_damping * omega_rad_s

        # Instantaneous raw commanded assistance
        self.tau_cmd = (self.k_aan * tau_deficit) - damping_torque

        # Real-time percentage distribution
        mag_cmd = abs(self.tau_cmd)
        mag_user = abs(tau_user)
        total = mag_cmd + mag_user + 1e-4

        self.assistance_percent = round((mag_cmd / total) * 100.0, 1)
        self.user_percent = round((mag_user / total) * 100.0, 1)

        return {
            "tau_cmd_unclamped": self.tau_cmd,
            "k_aan": round(self.k_aan, 3),
            "assistance_percent": self.assistance_percent,
            "user_percent": self.user_percent
        }

    def slow_loop_step(self, fatigue_index: float, user_effective_strength: float) -> Dict[str, float]:
        """Executes the 1-2 Hz outer adaptation loop.

        Adapts K_aan based on user participation, fatigue, and strength progression.
        """
        if not self.history_req_torque:
            return {"k_aan": self.k_aan}

        avg_req = sum(self.history_req_torque) / len(self.history_req_torque)
        avg_user = sum(self.history_user_torque) / len(self.history_user_torque)

        if avg_req > 0.5:
            self.recent_participation_ratio = min(1.0, avg_user / avg_req)
        else:
            self.recent_participation_ratio = user_effective_strength

        # Assist-As-Needed Adaptation Rule:
        # Target assistance is inversely proportional to user contribution
        target_k = 1.0 - (self.recent_participation_ratio * 0.85)

        # If fatigue is high, provide extra assistance boost
        if fatigue_index > DEFAULT_AAN.fatigue_threshold:
            fatigue_excess = (fatigue_index - DEFAULT_AAN.fatigue_threshold) / (1.0 - DEFAULT_AAN.fatigue_threshold)
            target_k += fatigue_excess * DEFAULT_AAN.fatigue_boost_factor

        # Bound target gain
        target_k = max(self.k_min, min(self.k_max, target_k))

        # Smooth exponential moving adaptation
        self.k_aan += self.adaptation_rate * (target_k - self.k_aan)
        self.k_aan = max(self.k_min, min(self.k_max, self.k_aan))

        return {
            "k_aan": round(self.k_aan, 3),
            "target_k": round(target_k, 3),
            "participation_ratio": round(self.recent_participation_ratio, 3)
        }
