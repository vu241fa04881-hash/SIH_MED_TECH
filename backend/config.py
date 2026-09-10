"""MoveAssist Configuration & Constants
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import os
from dataclasses import dataclass, field
from typing import Dict, Any

# Prominently displayed scientific disclaimer
SCIENTIFIC_DISCLAIMER: str = (
    "Virtual Engineering Prototype & Proof-of-Concept — "
    "Model estimates only, not direct biological measurements."
)

@dataclass
class AnthropometricDefaults:
    height_m: float = 1.75          # Total body height in meters
    mass_kg: float = 72.0           # Total body mass in kg
    thigh_length_ratio: float = 0.245  # Ratio of height (approx 0.43m for 1.75m)
    shank_length_ratio: float = 0.246  # Ratio of height (approx 0.43m for 1.75m)
    foot_length_ratio: float = 0.152   # Ratio of height (approx 0.26m for 1.75m)

@dataclass
class SafetyLimits:
    max_torque_nm: float = 35.0          # Absolute torque ceiling (|tau| <= 35 Nm)
    max_slew_rate_nm_per_s: float = 120.0 # Maximum allowed torque rate-of-change
    min_rom_deg: float = 0.0             # Anatomical full extension (degrees)
    max_rom_deg: float = 115.0           # Anatomical deep flexion limit (degrees)
    soft_rom_margin_deg: float = 5.0     # Buffer zone for soft damping pushback
    heartbeat_timeout_s: float = 0.25    # Maximum elapsed sensor period before safe fallback
    max_angular_velocity_deg_s: float = 360.0 # Upper physiological velocity boundary
    
    # Anti-Fall Controlled Soft E-Stop (30s to 2 minutes progressive deceleration)
    critical_fatigue_threshold: float = 0.85 # Muscle exhaustion threshold indicating imminent fall risk
    fatigue_acute_fall_threshold: float = 0.95 # Extreme exhaustion where immediate collapse/fall occurs (30s stop)
    fatigue_high_fall_threshold: float = 0.90  # Severe exhaustion (60s stop)
    controlled_soft_stop_default_duration_s: float = 90.0 # 1.5 min default
    soft_stop_min_duration_s: float = 30.0               # 30 seconds minimum (Rapid Anti-Buckle)
    soft_stop_max_duration_s: float = 120.0              # 2.0 min maximum
    anti_collapse_support_torque_nm: float = 18.0        # Sustained anti-buckling support torque


@dataclass
class AANParameters:
    base_aan_gain: float = 0.70          # Default nominal assistance gain K_aan [0.0, 1.0]
    min_aan_gain: float = 0.10           # Minimum assistance gain (active user)
    max_aan_gain: float = 0.95           # Maximum assistance gain (weak/fatigued user)
    adaptation_rate: float = 0.05        # Rate of gain adaptation per slow cycle
    fatigue_threshold: float = 0.40      # Fatigue index threshold where boost initiates
    fatigue_boost_factor: float = 0.35   # Additional gain scaling when muscle is fatigued

@dataclass
class ActuatorDynamics:
    motor_lag_time_const_s: float = 0.025  # 1st order lag tau (25 ms)
    torque_saturation_nm: float = 40.0     # Physical motor saturation limit
    damping_coeff: float = 0.15            # Motor back-EMF / viscous friction damping

@dataclass
class SimulationConfig:
    frequency_hz: float = 100.0          # Fast loop rate (100 Hz)
    dt: float = 0.01                     # 10 ms step size
    slow_loop_decimation: int = 50       # Slow loop executes every 50 fast steps (2 Hz)
    gravity: float = 9.80665             # Gravitational acceleration (m/s^2)
    butterworth_cutoff_hz: float = 6.0   # 2nd-order Butterworth cutoff frequency for derivatives
    
    server_host: str = os.getenv("HOST", "0.0.0.0")
    server_port: int = int(os.getenv("PORT", "8000"))

# Global default instances
DEFAULT_ANTHRO = AnthropometricDefaults()
DEFAULT_SAFETY = SafetyLimits()
DEFAULT_AAN = AANParameters()
DEFAULT_ACTUATOR = ActuatorDynamics()
DEFAULT_SIM = SimulationConfig()
