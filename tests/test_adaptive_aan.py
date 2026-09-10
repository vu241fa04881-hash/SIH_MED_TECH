"""Automated Verification of Adaptive Assist-As-Needed (AAN) Controller
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import unittest
from backend.controllers.adaptive_aan import AdaptiveAANController
from backend.controllers.deficit import AssistanceDeficitCalculator


class TestAdaptiveAAN(unittest.TestCase):

    def setUp(self):
        self.aan = AdaptiveAANController()
        self.deficit_calc = AssistanceDeficitCalculator()

    def test_deficit_calculation(self):
        """tau_deficit = max(0, tau_req - tau_user)."""
        # User supplies 5 Nm of 20 Nm required
        d1 = self.deficit_calc.compute(tau_required=20.0, tau_user_estimated=5.0)
        self.assertEqual(d1["tau_deficit"], 15.0)

        # User supplies 25 Nm of 20 Nm required (no deficit)
        d2 = self.deficit_calc.compute(tau_required=20.0, tau_user_estimated=25.0)
        self.assertEqual(d2["tau_deficit"], 0.0)

    def test_inverse_relationship_adaptation(self):
        """User contribution increases => Assistance gain K_aan decreases.

        User contribution decreases => Assistance gain K_aan increases.
        """
        # Case A: Active Strong User (User supplies 80% of required torque)
        self.aan.reset()
        initial_gain = self.aan.k_aan

        # Simulate 2 seconds of high user participation
        for _ in range(150):
            self.aan.fast_loop_step(tau_deficit=4.0, omega_deg_s=0.0, tau_user=16.0, tau_req=20.0)
            if _ % 20 == 0:
                self.aan.slow_loop_step(fatigue_index=0.05, user_effective_strength=0.80)

        gain_strong = self.aan.k_aan
        self.assertLess(gain_strong, initial_gain, "High user strength must reduce assistance gain")

        # Case B: Weak User (User supplies only 15% of required torque)
        for _ in range(250):
            self.aan.fast_loop_step(tau_deficit=17.0, omega_deg_s=0.0, tau_user=3.0, tau_req=20.0)
            if _ % 20 == 0:
                self.aan.slow_loop_step(fatigue_index=0.10, user_effective_strength=0.15)

        gain_weak = self.aan.k_aan
        self.assertGreater(gain_weak, gain_strong, "Low user strength must increase assistance gain")

    def test_fatigue_adaptation_boost(self):
        """High muscle fatigue triggers extra assistive boost."""
        self.aan.reset()
        initial_k = self.aan.k_aan

        # Simulate high fatigue (> 0.40)
        for _ in range(50):
            self.aan.fast_loop_step(tau_deficit=10.0, omega_deg_s=0.0, tau_user=10.0, tau_req=20.0)
        self.aan.slow_loop_step(fatigue_index=0.85, user_effective_strength=0.50)

        self.assertGreater(self.aan.k_aan, 0.50)


if __name__ == "__main__":
    unittest.main()
