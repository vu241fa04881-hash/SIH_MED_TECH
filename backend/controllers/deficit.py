"""Assistance Deficit Calculator
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

from typing import Dict, Any


class AssistanceDeficitCalculator:
    """Calculates the physical deficit between the biomechanically required torque

    and the voluntary torque estimated from the user:
    
    tau_deficit = max(0, tau_required - tau_user_estimated) (for positive extension/flexion drive)
    """

    def __init__(self):
        self.tau_deficit = 0.0
        self.deficit_ratio = 0.0

    def compute(self, tau_required: float, tau_user_estimated: float) -> Dict[str, float]:
        """Calculates instantaneous torque deficit."""
        # Check directional alignment
        if tau_required >= 0:
            # Positive demand (e.g. extension support against gravity/inertia)
            deficit = max(0.0, tau_required - tau_user_estimated)
        else:
            # Negative demand (e.g. flexion assistance or controlled lowering)
            deficit = min(0.0, tau_required - tau_user_estimated)

        self.tau_deficit = deficit

        # Normalized deficit ratio [0.0 to 1.0]
        denom = abs(tau_required) if abs(tau_required) > 0.5 else 1.0
        self.deficit_ratio = min(1.0, max(0.0, abs(deficit) / denom))

        return {
            "tau_deficit": round(self.tau_deficit, 3),
            "deficit_ratio": round(self.deficit_ratio, 3)
        }
