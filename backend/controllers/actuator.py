"""Virtual BLDC Motor Actuator Dynamics
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import math
from typing import Dict, Any
from backend.config import DEFAULT_ACTUATOR


class VirtualBLDCActuator:
    """Simulates a high-torque brushless DC (BLDC) motor with planetary harmonic drive:

    - First-order lag response: tau * d(T)/dt + T = T_cmd
    - Torque saturation
    - Back-EMF viscous friction
    - Thermal temperature model
    """

    def __init__(self, dt: float = 0.01):
        self.dt = dt
        self.tau = DEFAULT_ACTUATOR.motor_lag_time_const_s
        self.saturation_nm = DEFAULT_ACTUATOR.torque_saturation_nm
        self.damping_coeff = DEFAULT_ACTUATOR.damping_coeff

        self.actual_torque_nm = 0.0
        self.winding_temp_c = 32.0  # Ambient starts at 32 deg C
        self.ambient_temp_c = 25.0

    def reset(self) -> None:
        self.actual_torque_nm = 0.0
        self.winding_temp_c = 32.0

    def step(self, commanded_torque_nm: float, knee_velocity_deg_s: float) -> Dict[str, float]:
        """Advances actuator dynamics by dt."""
        # 1. First-order lag model (Euler discretization: T[k] = T[k-1] + (dt/tau)*(cmd - T[k-1]))
        alpha = self.dt / (self.tau + self.dt)
        raw_torque = self.actual_torque_nm + alpha * (commanded_torque_nm - self.actual_torque_nm)

        # 2. Back-EMF and viscous drag damping
        omega_rad_s = math.radians(knee_velocity_deg_s)
        drag_torque = self.damping_coeff * omega_rad_s
        net_torque = raw_torque - drag_torque

        # 3. Motor hardware saturation
        self.actual_torque_nm = max(-self.saturation_nm, min(self.saturation_nm, net_torque))

        # 4. Motor thermal estimation (Joule heating ~ I^2 * R proportional to tau^2)
        heat_in = 0.008 * (self.actual_torque_nm ** 2)
        heat_out = 0.003 * (self.winding_temp_c - self.ambient_temp_c)
        self.winding_temp_c += (heat_in - heat_out) * self.dt

        return {
            "actual_torque_nm": round(self.actual_torque_nm, 3),
            "commanded_torque_nm": round(commanded_torque_nm, 3),
            "motor_temp_c": round(self.winding_temp_c, 1)
        }
