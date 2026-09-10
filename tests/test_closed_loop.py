"""Automated Verification of Full Closed-Loop Simulation System
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import unittest
import math
from backend.simulation.loop import SimulationEngine


class TestClosedLoopSimulation(unittest.TestCase):

    def setUp(self):
        self.engine = SimulationEngine(dt=0.01)

    def test_simulation_step_execution_and_telemetry_schema(self):
        """Run 300 simulation cycles (3 full seconds) and verify telemetry consistency."""
        for step_idx in range(300):
            frame = self.engine.step()

            # Verify top-level structure
            self.assertIn("timestamp_s", frame)
            self.assertIn("kinematics", frame)
            self.assertIn("torques", frame)
            self.assertIn("aan", frame)
            self.assertIn("gait", frame)
            self.assertIn("sensors", frame)
            self.assertIn("safety", frame)
            self.assertIn("disclaimer", frame)

            # Check that no NaNs exist in any physical metric
            self.assertFalse(math.isnan(frame["kinematics"]["knee_angle_deg"]))
            self.assertFalse(math.isnan(frame["torques"]["required_nm"]))
            self.assertFalse(math.isnan(frame["torques"]["actuator_output_nm"]))
            self.assertFalse(math.isnan(frame["aan"]["assistance_percent"]))
            self.assertFalse(math.isnan(frame["aan"]["user_percent"]))

            # Verify range bounds
            self.assertGreaterEqual(frame["kinematics"]["knee_angle_deg"], -0.1)
            self.assertLessEqual(frame["kinematics"]["knee_angle_deg"], 115.1)
            self.assertLessEqual(abs(frame["torques"]["commanded_nm"]), 35.1)

    def test_automated_demo_runner_phases(self):
        """Verify automated demonstration advances cleanly through clinical phases."""
        self.engine.start_demo()
        self.assertTrue(self.engine.demo.is_active)

        # Run 700 steps (7 seconds) to verify transition from Phase 1 to Phase 2
        for _ in range(700):
            frame = self.engine.step()

        self.assertGreaterEqual(frame["demo"]["phase"], 2, "Demo should have transitioned to Phase 2")
        self.engine.stop_demo()
        self.assertFalse(self.engine.demo.is_active)

    def test_kinematic_movement_modes(self):
        """Verify all 5 kinematic movement modes (WALK, SIT_STAND, RUN, STANDBY, MANUAL_JOG)."""
        # 1. Test WALK
        self.engine.set_kinematic_mode("WALK")
        self.assertEqual(self.engine.kinematic_mode, "WALK")
        frame = self.engine.step()
        self.assertEqual(frame["kinematics"]["mode"], "WALK")

        # 2. Test STANDBY
        self.engine.set_kinematic_mode("STANDBY")
        self.assertEqual(self.engine.kinematic_mode, "STANDBY")
        frame = self.engine.step()
        self.assertEqual(frame["kinematics"]["mode"], "STANDBY")
        self.assertAlmostEqual(frame["kinematics"]["knee_angle_deg"], 10.0, delta=0.5)

        # 3. Test MANUAL_JOG
        self.engine.set_kinematic_mode("MANUAL_JOG", jog_angle_deg=45.0)
        self.assertEqual(self.engine.kinematic_mode, "MANUAL_JOG")
        frame = self.engine.step()
        self.assertEqual(frame["kinematics"]["mode"], "MANUAL_JOG")
        self.assertAlmostEqual(frame["kinematics"]["knee_angle_deg"], 45.0, delta=0.5)

        # 4. Test SIT_STAND
        self.engine.set_kinematic_mode("SIT_STAND")
        self.assertEqual(self.engine.kinematic_mode, "SIT_STAND")
        frame = self.engine.step()
        self.assertEqual(frame["kinematics"]["mode"], "SIT_STAND")

        # 5. Test RUN
        self.engine.set_kinematic_mode("RUN")
        self.assertEqual(self.engine.kinematic_mode, "RUN")
        frame = self.engine.step()
        self.assertEqual(frame["kinematics"]["mode"], "RUN")

    def test_power_and_assist_telemetry(self):
        """Verify human strength %, exo strength %, and robotic power telemetry."""
        self.engine.set_kinematic_mode("WALK")
        for _ in range(50):
            frame = self.engine.step()

        p = frame["power"]
        self.assertIn("mechanical_watts", p)
        self.assertIn("electrical_watts", p)
        self.assertIn("peak_watts", p)
        self.assertIn("cumulative_kj", p)
        self.assertIn("actuator_load_pct", p)
        self.assertIn("human_strength_used_pct", p)
        self.assertIn("exo_strength_used_pct", p)

        # Verify strength percentages sum to 100%
        total_pct = p["human_strength_used_pct"] + p["exo_strength_used_pct"]
        self.assertAlmostEqual(total_pct, 100.0, delta=0.5)

        # Power non-negativity and bounds
        self.assertGreaterEqual(p["mechanical_watts"], 0.0)
        self.assertGreaterEqual(p["electrical_watts"], 0.0)
        self.assertGreaterEqual(p["peak_watts"], 0.0)
        self.assertGreaterEqual(p["cumulative_kj"], 0.0)
        self.assertLessEqual(p["actuator_load_pct"], 100.0)


if __name__ == "__main__":
    unittest.main()

