"""Dempster/Winter Anthropometric Model & Auto-Calibration
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import math
from dataclasses import dataclass
from enum import Enum
from typing import Dict, Any, Tuple


class CalibrationState(str, Enum):
    UNINITIALIZED = "UNINITIALIZED"
    WEAR_DETECTED = "WEAR_DETECTED"
    ZERO_SENSORS = "ZERO_SENSORS"
    TARE_LOAD = "TARE_LOAD"
    CALIBRATED = "CALIBRATED"


@dataclass
class SegmentProperties:
    mass: float              # kg
    length: float            # m
    r_com_proximal: float    # m (distance from proximal joint to COM)
    moi_proximal: float      # kg*m^2 (Moment of Inertia about proximal joint)


class AnthropometricModel:
    """Calculates anatomical segment parameters based on standard Dempster (1955)

    and Winter (2009) biomechanical regression data.
    """

    def __init__(self, height_m: float = 1.75, mass_kg: float = 72.0):
        self.height_m = max(1.20, min(2.20, float(height_m)))
        self.mass_kg = max(35.0, min(160.0, float(mass_kg)))
        
        # Calibration state machine
        self.calibration_state = CalibrationState.CALIBRATED
        self.calibration_progress = 100.0  # Percentage 0-100
        self.calibration_step_timer = 0
        
        self.recompute_segments()

    def update_profile(self, height_m: float, mass_kg: float) -> None:
        """Update user parameters and recalculate segment masses, COM, and MOI."""
        self.height_m = max(1.20, min(2.20, float(height_m)))
        self.mass_kg = max(35.0, min(160.0, float(mass_kg)))
        self.recompute_segments()

    def recompute_segments(self) -> None:
        """Applies Dempster/Winter regression coefficients:

        - Thigh mass = 10.0% of total mass
        - Shank mass = 4.65% of total mass
        - Foot mass  = 1.45% of total mass
        - Thigh length = 0.245 * H
        - Shank length = 0.246 * H
        - Foot length  = 0.152 * H
        """
        H = self.height_m
        M = self.mass_kg

        # Segment lengths (m)
        L_thigh = 0.245 * H
        L_shank = 0.246 * H
        L_foot  = 0.152 * H

        # Segment masses (kg)
        m_thigh = 0.1000 * M
        m_shank = 0.0465 * M
        m_foot  = 0.0145 * M

        # Center of Mass (COM) distances from proximal joint (m)
        # Thigh: 0.433 from hip
        r_com_thigh = 0.433 * L_thigh
        # Shank: 0.433 from knee
        r_com_shank = 0.433 * L_shank
        # Foot: 0.500 of foot length from heel/ankle complex
        r_com_foot = 0.500 * L_foot

        # Radius of gyration (rho) about proximal joint:
        # Shank rho_prox = 0.528 * L_shank
        # Foot rho_com = 0.475 * L_foot
        rho_prox_shank = 0.528 * L_shank
        I_shank_knee = m_shank * (rho_prox_shank ** 2)

        # Foot moment of inertia about knee axis (via parallel axis theorem: I_knee = I_com + m*d^2)
        # Distance from knee to foot COM is approx L_shank + r_com_foot_vertical
        rho_com_foot = 0.475 * L_foot
        I_foot_com = m_foot * (rho_com_foot ** 2)
        d_knee_to_foot_com = L_shank + 0.04  # ~4cm ankle center offset
        I_foot_knee = I_foot_com + m_foot * (d_knee_to_foot_com ** 2)

        # Combined knee moment of inertia of lower limb segments (shank + foot)
        self.I_knee_total = I_shank_knee + I_foot_knee

        # Effective pendular COM distance of shank+foot combined from knee joint
        total_distal_mass = m_shank + m_foot
        self.r_com_distal = (m_shank * r_com_shank + m_foot * d_knee_to_foot_com) / total_distal_mass

        self.thigh = SegmentProperties(
            mass=m_thigh,
            length=L_thigh,
            r_com_proximal=r_com_thigh,
            moi_proximal=m_thigh * ((0.540 * L_thigh) ** 2)
        )

        self.shank = SegmentProperties(
            mass=m_shank,
            length=L_shank,
            r_com_proximal=r_com_shank,
            moi_proximal=I_shank_knee
        )

        self.foot = SegmentProperties(
            mass=m_foot,
            length=L_foot,
            r_com_proximal=r_com_foot,
            moi_proximal=I_foot_knee
        )

    def start_calibration(self) -> None:
        """Triggers the automated 4-step calibration sequence."""
        self.calibration_state = CalibrationState.WEAR_DETECTED
        self.calibration_progress = 10.0
        self.calibration_step_timer = 0

    def step_calibration(self, dt: float) -> Tuple[CalibrationState, float]:
        """Advances the auto-calibration sequence:

        WEAR_DETECTED -> ZERO_SENSORS -> TARE_LOAD -> CALIBRATED
        """
        if self.calibration_state == CalibrationState.CALIBRATED:
            return self.calibration_state, 100.0

        self.calibration_step_timer += dt

        if self.calibration_state == CalibrationState.WEAR_DETECTED:
            self.calibration_progress = min(35.0, 10.0 + self.calibration_step_timer * 25.0)
            if self.calibration_step_timer >= 1.0:
                self.calibration_state = CalibrationState.ZERO_SENSORS
                self.calibration_step_timer = 0

        elif self.calibration_state == CalibrationState.ZERO_SENSORS:
            self.calibration_progress = min(70.0, 35.0 + self.calibration_step_timer * 35.0)
            if self.calibration_step_timer >= 1.0:
                self.calibration_state = CalibrationState.TARE_LOAD
                self.calibration_step_timer = 0

        elif self.calibration_state == CalibrationState.TARE_LOAD:
            self.calibration_progress = min(100.0, 70.0 + self.calibration_step_timer * 30.0)
            if self.calibration_step_timer >= 1.0:
                self.calibration_state = CalibrationState.CALIBRATED
                self.calibration_progress = 100.0
                self.calibration_step_timer = 0

        return self.calibration_state, self.calibration_progress

    def get_summary(self) -> Dict[str, Any]:
        """Returns JSON-serializable dictionary of anthropometric properties."""
        return {
            "height_m": round(self.height_m, 2),
            "mass_kg": round(self.mass_kg, 1),
            "thigh": {
                "mass_kg": round(self.thigh.mass, 3),
                "length_m": round(self.thigh.length, 3),
                "r_com_m": round(self.thigh.r_com_proximal, 3),
            },
            "shank": {
                "mass_kg": round(self.shank.mass, 3),
                "length_m": round(self.shank.length, 3),
                "r_com_m": round(self.shank.r_com_proximal, 3),
            },
            "foot": {
                "mass_kg": round(self.foot.mass, 3),
                "length_m": round(self.foot.length, 3),
            },
            "total_distal_mass_kg": round(self.shank.mass + self.foot.mass, 3),
            "I_knee_total_kgm2": round(self.I_knee_total, 4),
            "r_com_distal_m": round(self.r_com_distal, 3),
            "calibration_state": self.calibration_state.value,
            "calibration_progress": round(self.calibration_progress, 1),
        }
