"""Virtual Tri-Zone Foot Pressure Sensors (FSRs)
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import math
import random
from typing import Dict, Any


class FootPressureSensorArray:
    """Simulates 3 Force Sensitive Resistors (FSRs) positioned under:

    1. Heel (Initial contact / loading response)
    2. Metatarsal / Ball of Foot (Mid-stance to terminal stance)
    3. Hallux / Toe (Pre-swing / push-off)
    """

    def __init__(self, patient_mass_kg: float = 72.0):
        self.mass_kg = patient_mass_kg
        self.nominal_bw_newtons = patient_mass_kg * 9.80665

        # Zones (Newtons)
        self.heel_force_n = 0.0
        self.metatarsal_force_n = 0.0
        self.toe_force_n = 0.0
        self.total_grf_n = 0.0

        # State detection
        self.is_stance = False
        self.contact_threshold_n = 25.0

        # Fault injection
        self.is_faulty = False
        self.fault_type = "NONE"

    def update_mass(self, mass_kg: float) -> None:
        self.mass_kg = mass_kg
        self.nominal_bw_newtons = mass_kg * 9.80665

    def inject_fault(self, fault_type: str = "DISCONNECTED") -> None:
        self.is_faulty = True
        self.fault_type = fault_type

    def clear_fault(self) -> None:
        self.is_faulty = False
        self.fault_type = "NONE"

    def update(self, gait_cycle_percent: float, is_stance_phase: bool) -> Dict[str, Any]:
        """Calculates realistic ground reaction forces across the 3 foot zones

        based on standard biomechanical gait force curves (Perry & Burnfield, 2010).
        """
        if self.is_faulty:
            return {
                "heel_n": 0.0 if self.fault_type == "DISCONNECTED" else 999.0,
                "metatarsal_n": 0.0 if self.fault_type == "DISCONNECTED" else 999.0,
                "toe_n": 0.0 if self.fault_type == "DISCONNECTED" else 999.0,
                "total_grf_n": 0.0 if self.fault_type == "DISCONNECTED" else 2997.0,
                "is_stance": False,
                "status": f"FAULT_{self.fault_type}",
                "healthy": False
            }

        if not is_stance_phase:
            # Swing phase: Foot is in the air, minimal baseline noise
            self.heel_force_n = max(0.0, random.gauss(1.5, 0.5))
            self.metatarsal_force_n = max(0.0, random.gauss(1.5, 0.5))
            self.toe_force_n = max(0.0, random.gauss(1.0, 0.4))
            self.total_grf_n = self.heel_force_n + self.metatarsal_force_n + self.toe_force_n
            self.is_stance = False
            return {
                "heel_n": round(self.heel_force_n, 1),
                "metatarsal_n": round(self.metatarsal_force_n, 1),
                "toe_n": round(self.toe_force_n, 1),
                "total_grf_n": round(self.total_grf_n, 1),
                "is_stance": False,
                "status": "HEALTHY",
                "healthy": True
            }

        # Stance phase: Map progress within stance (0% to 60% of total gait cycle)
        # Normalize stance progress: 0.0 (heel strike) to 1.0 (toe off)
        p = min(1.0, max(0.0, gait_cycle_percent / 60.0))
        bw = self.nominal_bw_newtons

        # Biomechanical Ground Reaction Force double-bump profile:
        # 1. Heel strike absorption: 0.0 <= p <= 0.35
        # 2. Metatarsal roll-over:   0.20 <= p <= 0.85
        # 3. Toe push-off:           0.65 <= p <= 1.0

        if p < 0.30:
            # Heel dominates
            h_ratio = math.sin((p / 0.30) * math.pi)
            self.heel_force_n = bw * 0.95 * h_ratio
            self.metatarsal_force_n = bw * 0.15 * p
            self.toe_force_n = 0.0
        elif p < 0.70:
            # Mid-stance to Terminal stance: Metatarsal roll-over
            sub_p = (p - 0.30) / 0.40
            self.heel_force_n = max(0.0, bw * 0.5 * (1.0 - sub_p))
            self.metatarsal_force_n = bw * (0.65 + 0.40 * math.sin(sub_p * math.pi))
            self.toe_force_n = bw * 0.30 * sub_p
        else:
            # Pre-swing push-off: Toe dominates
            sub_p = (p - 0.70) / 0.30
            self.heel_force_n = 0.0
            self.metatarsal_force_n = max(0.0, bw * 0.70 * (1.0 - sub_p))
            self.toe_force_n = bw * 1.05 * math.sin(sub_p * math.pi)

        # Add modest measurement noise
        self.heel_force_n = max(0.0, self.heel_force_n + random.gauss(0, 3.0))
        self.metatarsal_force_n = max(0.0, self.metatarsal_force_n + random.gauss(0, 3.0))
        self.toe_force_n = max(0.0, self.toe_force_n + random.gauss(0, 3.0))

        self.total_grf_n = self.heel_force_n + self.metatarsal_force_n + self.toe_force_n
        self.is_stance = self.total_grf_n > self.contact_threshold_n

        return {
            "heel_n": round(self.heel_force_n, 1),
            "metatarsal_n": round(self.metatarsal_force_n, 1),
            "toe_n": round(self.toe_force_n, 1),
            "total_grf_n": round(self.total_grf_n, 1),
            "is_stance": self.is_stance,
            "status": "HEALTHY",
            "healthy": True
        }
