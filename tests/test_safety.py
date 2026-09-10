"""Automated Verification of MoveAssist Safety Supervisor
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import unittest
from backend.safety.supervisor import SafetySupervisor, SafetyMode


class TestSafetySupervisor(unittest.TestCase):

    def setUp(self):
        self.safety = SafetySupervisor(dt=0.01)

    def test_torque_ceiling_clamping(self):
        """Ensure commanded torque never breaches +/- 35.0 Nm."""
        # Test extreme positive command
        res_pos = self.safety.process(
            raw_cmd_torque=90.0,
            knee_angle_deg=45.0,
            knee_vel_deg_s=0.0,
            sensors_healthy=True
        )
        self.assertLessEqual(res_pos["safe_torque_nm"], 35.0)

        # Test extreme negative command
        self.safety.prev_safe_torque = -20.0
        res_neg = self.safety.process(
            raw_cmd_torque=-90.0,
            knee_angle_deg=45.0,
            knee_vel_deg_s=0.0,
            sensors_healthy=True
        )
        self.assertGreaterEqual(res_neg["safe_torque_nm"], -35.0)

    def test_slew_rate_limiter(self):
        """Ensure torque jumps are clamped to max_slew_rate (120 Nm/s => 1.2 Nm per 0.01s step)."""
        self.safety.prev_safe_torque = 0.0
        # Command sudden step of +30.0 Nm
        res = self.safety.process(
            raw_cmd_torque=30.0,
            knee_angle_deg=45.0,
            knee_vel_deg_s=0.0,
            sensors_healthy=True
        )
        # In 0.01s, max delta is 120 * 0.01 = 1.2 Nm
        self.assertAlmostEqual(res["safe_torque_nm"], 1.2, delta=0.01)

    def test_anatomical_rom_limits(self):
        """Ensure boundary enforcement stops torque that would drive joint past 0 or 115 deg."""
        # At hyperextension boundary (0.0 deg), positive extension torque must be blocked
        res_ext = self.safety.process(
            raw_cmd_torque=15.0,
            knee_angle_deg=0.0,
            knee_vel_deg_s=0.0,
            sensors_healthy=True
        )
        self.assertLessEqual(res_ext["safe_torque_nm"], 0.0)

        # At deep flexion boundary (115.0 deg), negative flexion torque must be blocked
        self.safety.prev_safe_torque = 0.0
        res_flex = self.safety.process(
            raw_cmd_torque=-15.0,
            knee_angle_deg=115.0,
            knee_vel_deg_s=0.0,
            sensors_healthy=True
        )
        self.assertGreaterEqual(res_flex["safe_torque_nm"], 0.0)

    def test_emergency_stop_latch_and_instant_zero_torque(self):
        """Ensure E-Stop instantly cuts torque to zero and latches."""
        self.safety.prev_safe_torque = 20.0
        self.safety.trigger_estop("TEST_ESTOP")

        res = self.safety.process(
            raw_cmd_torque=25.0,
            knee_angle_deg=45.0,
            knee_vel_deg_s=0.0,
            sensors_healthy=True
        )
        self.assertEqual(res["safe_torque_nm"], 0.0)
        self.assertEqual(res["mode"], SafetyMode.EMERGENCY_STOP.value)
        self.assertTrue(res["e_stop_latched"])

        # Resetting should restore normal operation
        self.assertTrue(self.safety.reset_estop())
        self.assertFalse(self.safety.e_stop_latched)

    def test_sensor_fault_safe_fallback_mode(self):
        """Ensure sensor fault engages SAFE_FALLBACK mode."""
        res = self.safety.process(
            raw_cmd_torque=25.0,
            knee_angle_deg=45.0,
            knee_vel_deg_s=10.0,
            sensors_healthy=False
        )
        self.assertEqual(res["mode"], SafetyMode.SAFE_FALLBACK.value)
        self.assertLessEqual(abs(res["safe_torque_nm"]), 8.0)

    def test_controlled_soft_stop_progressive_deceleration_and_support(self):
        """Verify Controlled Soft E-Stop provides anti-collapse holding torque rather than 0."""
        self.safety.trigger_controlled_soft_stop(duration_s=60.0, reason="TEST_SOFT_STOP")
        self.assertTrue(self.safety.soft_stop_active)
        self.assertEqual(self.safety.mode, SafetyMode.CONTROLLED_SOFT_STOP)

        # Process a step
        res = self.safety.process(
            raw_cmd_torque=12.0,
            knee_angle_deg=35.0,
            knee_vel_deg_s=0.0,
            sensors_healthy=True
        )
        self.assertEqual(res["mode"], SafetyMode.CONTROLLED_SOFT_STOP.value)
        self.assertTrue(res["controlled_soft_stop"]["active"])
        self.assertGreater(res["safe_torque_nm"], 0.0, "Must provide positive anti-collapse holding torque")

        # Advance to completion (60s => 6000 steps)
        for _ in range(6000):
            res = self.safety.process(
                raw_cmd_torque=12.0,
                knee_angle_deg=35.0,
                knee_vel_deg_s=0.0,
                sensors_healthy=True
            )
        self.assertAlmostEqual(res["controlled_soft_stop"]["progress_pct"], 100.0, places=0)
        self.assertAlmostEqual(res["safe_torque_nm"], self.safety.anti_collapse_torque, delta=1.5)

    def test_controlled_soft_stop_30s_duration(self):
        """Verify Controlled Soft E-Stop can stop at 30 seconds with full anti-collapse support."""
        self.safety.trigger_controlled_soft_stop(duration_s=30.0, reason="TEST_30S_RAPID_STOP")
        self.assertTrue(self.safety.soft_stop_active)
        self.assertEqual(self.safety.soft_stop_duration_s, 30.0)

        # Step through 30 seconds (3000 steps at dt=0.01)
        for _ in range(3000):
            res = self.safety.process(
                raw_cmd_torque=15.0,
                knee_angle_deg=25.0,
                knee_vel_deg_s=0.0,
                sensors_healthy=True
            )
        self.assertAlmostEqual(res["controlled_soft_stop"]["progress_pct"], 100.0, places=0)
        self.assertAlmostEqual(res["safe_torque_nm"], self.safety.anti_collapse_torque, delta=1.5)

    def test_critical_muscle_fatigue_fall_prevention_trigger(self):
        """Verify critical muscle fatigue (fatigue >= 85%) automatically triggers Controlled Soft Stop."""
        from backend.simulation.loop import SimulationEngine
        engine = SimulationEngine(dt=0.01)
        
        # Inject critical muscle fatigue
        engine.set_user_parameters(fatigue=0.92)
        frame = engine.step()

        self.assertTrue(frame["safety"]["imminent_fall_risk"])
        self.assertTrue(frame["safety"]["controlled_soft_stop"]["active"])
        self.assertEqual(frame["safety"]["mode"], SafetyMode.CONTROLLED_SOFT_STOP.value)

    def test_fatigue_seriousness_adaptive_duration_and_dynamic_timer_escalation(self):
        """Verify:
        1. Moderate fatigue (88%) starts a 90s gradual stop.
        2. Escalation to acute fatigue (96%) dynamically updates the active timer down to 30s."""
        from backend.simulation.loop import SimulationEngine
        engine = SimulationEngine(dt=0.01)

        # 1. Inject moderate fatigue (88%) -> Elevated fall risk -> 90s stop
        engine.set_user_parameters(fatigue=0.88)
        frame1 = engine.step()
        self.assertTrue(frame1["safety"]["controlled_soft_stop"]["active"])
        self.assertEqual(frame1["safety"]["controlled_soft_stop"]["duration_s"], 90.0)
        self.assertEqual(frame1["safety"]["fall_seriousness"], "ELEVATED")

        # Run 5 seconds (500 steps)
        for _ in range(500):
            engine.step()

        # 2. Patient fatigue worsens to acute collapse danger (96%)
        engine.set_user_parameters(fatigue=0.96)
        frame2 = engine.step()

        # The supervisor must have dynamically updated the active timer down to 30s!
        self.assertEqual(frame2["safety"]["controlled_soft_stop"]["duration_s"], 30.0)
        self.assertEqual(frame2["safety"]["fall_seriousness"], "ACUTE_IMMEDIATE_FALL")
        self.assertLessEqual(frame2["safety"]["controlled_soft_stop"]["remaining_s"], 30.0)


if __name__ == "__main__":
    unittest.main()
