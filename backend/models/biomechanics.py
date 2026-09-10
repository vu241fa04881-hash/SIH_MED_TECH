"""Biomechanical Knee Torque Model & Butterworth Low-Pass Filter
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import math
from typing import Dict, Any, Tuple
from backend.models.anthropometry import AnthropometricModel
from backend.config import DEFAULT_SIM, SCIENTIFIC_DISCLAIMER


class Butterworth2ndOrder:
    """Online 2nd-order low-pass Butterworth filter for real-time numerical derivatives.

    Prevents high-frequency differentiation noise and spikes from destabilizing torque commands.
    """

    def __init__(self, cutoff_hz: float = 6.0, sample_rate_hz: float = 100.0):
        self.fc = cutoff_hz
        self.fs = sample_rate_hz
        
        # Prewarp frequency via bilinear transform
        c = 1.0 / math.tan(math.pi * self.fc / self.fs)
        c2 = c * c
        sqrt2_c = math.sqrt(2.0) * c
        
        a0 = 1.0 + sqrt2_c + c2
        self.b0 = 1.0 / a0
        self.b1 = 2.0 / a0
        self.b2 = 1.0 / a0
        self.a1 = (2.0 * (1.0 - c2)) / a0
        self.a2 = (1.0 - sqrt2_c + c2) / a0
        
        # State variables for direct form II
        self.x1 = 0.0
        self.x2 = 0.0
        self.y1 = 0.0
        self.y2 = 0.0

    def reset(self, initial_val: float = 0.0) -> None:
        """Reset internal filter states."""
        self.x1 = initial_val
        self.x2 = initial_val
        self.y1 = initial_val
        self.y2 = initial_val

    def process(self, x: float) -> float:
        """Apply difference equation:

        y[n] = b0*x[n] + b1*x[n-1] + b2*x[n-2] - a1*y[n-1] - a2*y[n-2]
        """
        y = (self.b0 * x + self.b1 * self.x1 + self.b2 * self.x2
             - self.a1 * self.y1 - self.a2 * self.y2)
        
        # Shift states
        self.x2 = self.x1
        self.x1 = x
        self.y2 = self.y1
        self.y1 = y
        return y


class BiomechanicalKneeModel:
    """Calculates theoretical required knee joint torque:

    tau_required = tau_gravity + tau_inertial + tau_external
    
    Includes 2nd-order Butterworth filtering on angular velocity and acceleration.
    Designated as a model estimate, not direct biological measurement.
    """

    def __init__(self, anthro: AnthropometricModel, dt: float = 0.01):
        self.anthro = anthro
        self.dt = dt
        self.gravity = DEFAULT_SIM.gravity

        # Online filters
        self.vel_filter = Butterworth2ndOrder(cutoff_hz=DEFAULT_SIM.butterworth_cutoff_hz, sample_rate_hz=1.0/dt)
        self.acc_filter = Butterworth2ndOrder(cutoff_hz=DEFAULT_SIM.butterworth_cutoff_hz, sample_rate_hz=1.0/dt)

        # Kinematic history
        self.prev_theta_rad = 0.0
        self.prev_omega_filtered = 0.0

        # Output states
        self.tau_gravity = 0.0
        self.tau_inertial = 0.0
        self.tau_external = 0.0
        self.tau_required = 0.0
        
        self.omega_raw = 0.0
        self.omega_filtered = 0.0
        self.alpha_raw = 0.0
        self.alpha_filtered = 0.0

    def reset(self, initial_theta_deg: float = 0.0) -> None:
        initial_rad = math.radians(initial_theta_deg)
        self.prev_theta_rad = initial_rad
        self.prev_omega_filtered = 0.0
        self.vel_filter.reset(0.0)
        self.acc_filter.reset(0.0)

    def step(self, theta_deg: float, external_force_n: float = 0.0,
             thigh_angle_deg: float = 0.0) -> Dict[str, float]:
        """Calculates instantaneous required knee torque for the given joint state.

        
        theta_deg: Knee flexion angle (0 = full extension, positive = flexion)
        external_force_n: External contact force / ground reaction component
        thigh_angle_deg: Absolute thigh orientation relative to vertical
        """
        theta_rad = math.radians(theta_deg)
        thigh_rad = math.radians(thigh_angle_deg)
        
        # Absolute shank angle relative to gravity vertical:
        # phi_shank = thigh_angle - knee_flexion
        phi_shank = thigh_rad - theta_rad

        # 1. Numerical derivatives with dt
        self.omega_raw = (theta_rad - self.prev_theta_rad) / self.dt
        self.omega_filtered = self.vel_filter.process(self.omega_raw)

        self.alpha_raw = (self.omega_filtered - self.prev_omega_filtered) / self.dt
        self.alpha_filtered = self.acc_filter.process(self.alpha_raw)

        self.prev_theta_rad = theta_rad
        self.prev_omega_filtered = self.omega_filtered

        # 2. Gravitational Torque Component:
        # tau_gravity = (m_shank * r_com_shank + m_foot * d_foot) * g * sin(phi_shank)
        # Using anthropometric distal moment of mass:
        m_distal = self.anthro.shank.mass + self.anthro.foot.mass
        r_distal = self.anthro.r_com_distal
        
        # Gravitational torque acting around knee:
        self.tau_gravity = m_distal * r_distal * self.gravity * math.sin(phi_shank)

        # 3. Inertial Torque Component:
        # tau_inertial = I_knee * alpha
        self.tau_inertial = self.anthro.I_knee_total * self.alpha_filtered

        # 4. External Torque Component:
        # Ground reaction or external load transmitted along shank lever arm
        self.tau_external = external_force_n * (self.anthro.shank.length * 0.15)

        # 5. Total Required Knee Torque:
        self.tau_required = self.tau_gravity + self.tau_inertial + self.tau_external

        return {
            "tau_required": self.tau_required,
            "tau_gravity": self.tau_gravity,
            "tau_inertial": self.tau_inertial,
            "tau_external": self.tau_external,
            "omega_deg_s": math.degrees(self.omega_filtered),
            "alpha_deg_s2": math.degrees(self.alpha_filtered),
            "disclaimer": SCIENTIFIC_DISCLAIMER
        }
