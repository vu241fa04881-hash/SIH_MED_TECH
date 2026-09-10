"""5-Phase Automated Clinical Demonstration Engine
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

from enum import IntEnum
from typing import Dict, Any, Tuple


class DemoPhase(IntEnum):
    IDLE = 0
    PHASE_1_WEAK_PATIENT = 1
    PHASE_2_IMPROVEMENT = 2
    PHASE_3_FATIGUE = 3
    PHASE_4_DETERIORATION = 4
    PHASE_5_RECOVERY = 5


class AutomatedDemoRunner:
    """Orchestrates the 5-phase clinical demonstration:

    1. Phase 1: Weak Patient (Strength 20% => High AAN Assistance ~85%)
    2. Phase 2: Patient Improvement (Strength increases to 70% => Assistance smoothly decreases)
    3. Phase 3: Muscle Fatigue (Fatigue accumulates => Assistance automatically ramps up)
    4. Phase 4: Sudden Deterioration (Tremor/spasm injected => Safety Supervisor enters Protective Mode)
    5. Phase 5: Recovery (Stabilization => System returns to normal adaptive baseline)
    """

    def __init__(self):
        self.is_active = False
        self.current_phase = DemoPhase.IDLE
        self.phase_elapsed_s = 0.0
        self.total_elapsed_s = 0.0

        # Phase durations in seconds
        self.phase_durations = {
            DemoPhase.PHASE_1_WEAK_PATIENT: 6.0,
            DemoPhase.PHASE_2_IMPROVEMENT: 7.0,
            DemoPhase.PHASE_3_FATIGUE: 6.0,
            DemoPhase.PHASE_4_DETERIORATION: 5.0,
            DemoPhase.PHASE_5_RECOVERY: 6.0,
        }

        self.phase_descriptions = {
            DemoPhase.IDLE: "Standby / Manual Interactive Mode",
            DemoPhase.PHASE_1_WEAK_PATIENT: "Phase 1: Weak Patient — Low voluntary strength (20%). Exoskeleton delivers high assistive torque (~85%).",
            DemoPhase.PHASE_2_IMPROVEMENT: "Phase 2: Patient Improvement — Voluntary strength rises to 70%. Exoskeleton automatically decreases assistance (~30%) to encourage active participation.",
            DemoPhase.PHASE_3_FATIGUE: "Phase 3: Muscle Fatigue — Sustained repetitions induce neuromuscular fatigue. System detects capacity drop and boosts assistance.",
            DemoPhase.PHASE_4_DETERIORATION: "Phase 4: Sudden Deterioration — Spastic tremor detected! Safety Supervisor engages Protective Mode with active viscous stabilization.",
            DemoPhase.PHASE_5_RECOVERY: "Phase 5: Recovery & Re-adaptation — Spasm clears, kinematics stabilize, smooth return to normal Assist-As-Needed mode."
        }

    def start(self) -> None:
        self.is_active = True
        self.current_phase = DemoPhase.PHASE_1_WEAK_PATIENT
        self.phase_elapsed_s = 0.0
        self.total_elapsed_s = 0.0

    def stop(self) -> None:
        self.is_active = False
        self.current_phase = DemoPhase.IDLE
        self.phase_elapsed_s = 0.0

    def step(self, dt: float) -> Tuple[DemoPhase, Dict[str, Any]]:
        """Advances the demonstration sequence and returns target patient parameters."""
        if not self.is_active or self.current_phase == DemoPhase.IDLE:
            return DemoPhase.IDLE, {
                "active": False,
                "phase": 0,
                "name": "MANUAL_MODE",
                "description": self.phase_descriptions[DemoPhase.IDLE],
                "progress_percent": 0.0
            }

        self.phase_elapsed_s += dt
        self.total_elapsed_s += dt
        duration = self.phase_durations[self.current_phase]
        progress = min(1.0, self.phase_elapsed_s / duration)

        target_strength = 0.35
        target_fatigue = 0.0
        spasm_active = False

        if self.current_phase == DemoPhase.PHASE_1_WEAK_PATIENT:
            # Low strength (0.18 to 0.22), low fatigue
            target_strength = 0.20
            target_fatigue = 0.05
            spasm_active = False
            if self.phase_elapsed_s >= duration:
                self.current_phase = DemoPhase.PHASE_2_IMPROVEMENT
                self.phase_elapsed_s = 0.0

        elif self.current_phase == DemoPhase.PHASE_2_IMPROVEMENT:
            # Patient strength ramps from 0.20 to 0.72
            target_strength = 0.20 + (0.52 * progress)
            target_fatigue = 0.08
            spasm_active = False
            if self.phase_elapsed_s >= duration:
                self.current_phase = DemoPhase.PHASE_3_FATIGUE
                self.phase_elapsed_s = 0.0

        elif self.current_phase == DemoPhase.PHASE_3_FATIGUE:
            # Patient strength starts high but fatigue accumulates rapidly from 0.10 to 0.85
            target_strength = 0.70
            target_fatigue = 0.10 + (0.75 * progress)
            spasm_active = False
            if self.phase_elapsed_s >= duration:
                self.current_phase = DemoPhase.PHASE_4_DETERIORATION
                self.phase_elapsed_s = 0.0

        elif self.current_phase == DemoPhase.PHASE_4_DETERIORATION:
            # Spasm tremor injected
            target_strength = 0.40
            target_fatigue = 0.60
            spasm_active = True
            if self.phase_elapsed_s >= duration:
                self.current_phase = DemoPhase.PHASE_5_RECOVERY
                self.phase_elapsed_s = 0.0

        elif self.current_phase == DemoPhase.PHASE_5_RECOVERY:
            # Recovery and return to baseline
            target_strength = 0.40 + (0.10 * progress)
            target_fatigue = max(0.15, 0.60 * (1.0 - progress))
            spasm_active = False
            if self.phase_elapsed_s >= duration:
                # Complete demonstration loop
                self.is_active = False
                self.current_phase = DemoPhase.IDLE
                self.phase_elapsed_s = 0.0

        return self.current_phase, {
            "active": self.is_active,
            "phase": int(self.current_phase),
            "name": self.current_phase.name,
            "description": self.phase_descriptions[self.current_phase],
            "progress_percent": round(progress * 100.0, 1),
            "total_elapsed_s": round(self.total_elapsed_s, 2),
            "target_strength": round(target_strength, 3),
            "target_fatigue": round(target_fatigue, 3),
            "spasm_active": spasm_active
        }
