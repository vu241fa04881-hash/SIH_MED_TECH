"""Virtual Surface Electromyography (sEMG) Sensor
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import math
import random
from typing import Dict, Any


class VirtualsEMG:
    """Simulates surface EMG electrodes placed over the Quadriceps (Rectus Femoris)

    and Hamstrings (Biceps Femoris).
    Generates realistic biological raw interference signals, linear envelope RMS,
    and median spectral frequency shift indicating neuromuscular fatigue.
    """

    def __init__(self):
        self.sample_idx = 0
        self.median_frequency_hz = 110.0  # Fresh muscle nominal MDF
        self.raw_microvolts = 0.0
        self.envelope_mv = 0.0

        # Fault simulation
        self.is_faulty = False
        self.fault_type = "NONE"

    def inject_fault(self, fault_type: str = "DETACHED") -> None:
        self.is_faulty = True
        self.fault_type = fault_type

    def clear_fault(self) -> None:
        self.is_faulty = False
        self.fault_type = "NONE"

    def update(self, voluntary_activation: float, fatigue_index: float) -> Dict[str, Any]:
        """Simulates raw EMG bandpass filtered signal and root-mean-square (RMS) envelope."""
        if self.is_faulty:
            return {
                "raw_uV": 0.0 if self.fault_type == "DETACHED" else 2500.0,
                "envelope_norm": 0.0 if self.fault_type == "DETACHED" else 1.0,
                "median_freq_hz": 0.0,
                "status": f"FAULT_{self.fault_type}",
                "healthy": False
            }

        self.sample_idx += 1
        
        # 1. Median frequency downshifts with fatigue (classic spectral fatigue indicator: 110Hz -> 65Hz)
        self.median_frequency_hz = 110.0 - (45.0 * fatigue_index)

        # 2. Raw interference signal simulation (superposition of motor unit action potentials)
        # Biological bandwidth: 20 Hz to 450 Hz
        t = self.sample_idx * 0.01
        carrier1 = math.sin(2.0 * math.pi * self.median_frequency_hz * t)
        carrier2 = math.sin(2.0 * math.pi * (self.median_frequency_hz * 0.6) * t)
        noise = random.gauss(0, 0.2)

        # Voltage scale: baseline noise ~ 10-25 uV, max contraction ~ 800-1500 uV
        norm_activation = max(0.02, min(1.0, voluntary_activation))
        raw_amplitude_uV = norm_activation * 1200.0 * (carrier1 * 0.6 + carrier2 * 0.4 + noise)
        self.raw_microvolts = raw_amplitude_uV

        # 3. RMS Envelope: smoothed positive amplitude
        self.envelope_norm = norm_activation + (random.gauss(0, 0.02))
        self.envelope_norm = max(0.0, min(1.0, self.envelope_norm))

        return {
            "raw_uV": round(self.raw_microvolts, 1),
            "envelope_norm": round(self.envelope_norm, 3),
            "median_freq_hz": round(self.median_frequency_hz, 1),
            "status": "HEALTHY",
            "healthy": True
        }
