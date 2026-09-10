"""Virtual 6-Axis Inertial Measurement Unit (IMU)
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import math
import random
from typing import Dict, Any


class VirtualIMU:
    """Simulates a 6-axis MEMS IMU (3-axis Gyroscope + 3-axis Accelerometer)

    mounted on thigh or shank segments.
    Features realistic sensor noise, bias drift, and fault injection hooks.
    """

    def __init__(self, name: str, gyro_noise_std: float = 0.02, accel_noise_std: float = 0.05):
        self.name = name
        self.gyro_noise_std = gyro_noise_std
        self.accel_noise_std = accel_noise_std
        
        # Bias drift
        self.gyro_bias = 0.005
        self.accel_bias = 0.01

        # Sensor Fault Injection
        self.is_faulty = False
        self.fault_type = "NONE"  # "DROPOUT", "FREEZE", "SATURATION", "NOISE_SPIKE"
        self.last_valid_reading: Dict[str, float] = {}

    def inject_fault(self, fault_type: str = "DROPOUT") -> None:
        self.is_faulty = True
        self.fault_type = fault_type

    def clear_fault(self) -> None:
        self.is_faulty = False
        self.fault_type = "NONE"

    def update(self, angle_rad: float, omega_rad_s: float, alpha_rad_s2: float,
               gravity: float = 9.80665) -> Dict[str, Any]:
        """Update sensor reading given segment state."""
        # Check fault injection
        if self.is_faulty:
            if self.fault_type == "DROPOUT":
                return {
                    "sensor": self.name,
                    "status": "FAULT_DROPOUT",
                    "gyro_z_deg_s": float("nan"),
                    "accel_x_g": float("nan"),
                    "accel_y_g": float("nan"),
                    "pitch_deg": float("nan"),
                    "healthy": False
                }
            elif self.fault_type == "FREEZE" and self.last_valid_reading:
                frozen = self.last_valid_reading.copy()
                frozen["status"] = "FAULT_FROZEN"
                frozen["healthy"] = False
                return frozen
            elif self.fault_type == "SATURATION":
                return {
                    "sensor": self.name,
                    "status": "FAULT_SATURATED",
                    "gyro_z_deg_s": 2000.0,
                    "accel_x_g": 16.0,
                    "accel_y_g": 16.0,
                    "pitch_deg": 180.0,
                    "healthy": False
                }

        # Nominal physical measurements:
        # Gyroscope measures angular velocity around Z (sagittal plane)
        gyro_clean = math.degrees(omega_rad_s)
        gyro_noisy = gyro_clean + self.gyro_bias + random.gauss(0, self.gyro_noise_std * 57.3)

        # Accelerometer measures dynamic acceleration + gravity projection
        # Accel X is parallel to limb segment, Accel Y is perpendicular
        accel_x_clean = gravity * math.cos(angle_rad)
        accel_y_clean = gravity * math.sin(angle_rad) + (alpha_rad_s2 * 0.25)

        accel_x_noisy = (accel_x_clean / gravity) + random.gauss(0, self.accel_noise_std)
        accel_y_noisy = (accel_y_clean / gravity) + random.gauss(0, self.accel_noise_std)

        pitch_deg = math.degrees(angle_rad) + random.gauss(0, 0.1)

        reading = {
            "sensor": self.name,
            "status": "HEALTHY",
            "gyro_z_deg_s": round(gyro_noisy, 2),
            "accel_x_g": round(accel_x_noisy, 3),
            "accel_y_g": round(accel_y_noisy, 3),
            "pitch_deg": round(pitch_deg, 2),
            "healthy": True
        }
        self.last_valid_reading = reading
        return reading
