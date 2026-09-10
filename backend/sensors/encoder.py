"""Joint Optical Encoder Model
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import math
from typing import Dict, Any


class OpticalJointEncoder:
    """Simulates a high-resolution quadrature optical joint angle encoder

    (12-bit / 4096 CPR => approx 0.088 deg per count).
    """

    def __init__(self, resolution_deg: float = 0.088, dt: float = 0.01):
        self.resolution_deg = resolution_deg
        self.dt = dt
        self.prev_quantized_deg = 0.0

        # Fault simulation
        self.is_faulty = False
        self.fault_type = "NONE"

    def inject_fault(self, fault_type: str = "SIGNAL_LOSS") -> None:
        self.is_faulty = True
        self.fault_type = fault_type

    def clear_fault(self) -> None:
        self.is_faulty = False
        self.fault_type = "NONE"

    def update(self, true_knee_angle_deg: float) -> Dict[str, Any]:
        """Quantizes continuous angle to optical encoder steps and computes velocity."""
        if self.is_faulty:
            return {
                "angle_deg": float("nan") if self.fault_type == "SIGNAL_LOSS" else 0.0,
                "velocity_deg_s": 0.0,
                "raw_counts": 0,
                "status": f"FAULT_{self.fault_type}",
                "healthy": False
            }

        # Quantize to discrete encoder resolution
        counts = round(true_knee_angle_deg / self.resolution_deg)
        quantized_deg = counts * self.resolution_deg

        # Discrete differentiation
        velocity_deg_s = (quantized_deg - self.prev_quantized_deg) / self.dt
        self.prev_quantized_deg = quantized_deg

        return {
            "angle_deg": round(quantized_deg, 2),
            "velocity_deg_s": round(velocity_deg_s, 2),
            "raw_counts": counts,
            "status": "HEALTHY",
            "healthy": True
        }
