"""Automated Verification of Biomechanical Torque Equations & Filter
SIH 2026 | PS SIH26113 | Team: BERSERK TECHIES | Team ID: TEAM-147
"""

import unittest
import math
import random
from backend.models.anthropometry import AnthropometricModel
from backend.models.biomechanics import BiomechanicalKneeModel, Butterworth2ndOrder


class TestBiomechanics(unittest.TestCase):

    def setUp(self):
        self.anthro = AnthropometricModel(height_m=1.75, mass_kg=72.0)
        self.biomech = BiomechanicalKneeModel(self.anthro, dt=0.01)

    def test_anthropometric_regression_proportions(self):
        """Verify Dempster/Winter mass and length ratios."""
        m_total = self.anthro.mass_kg
        h_total = self.anthro.height_m

        # Thigh mass ~ 10%
        self.assertAlmostEqual(self.anthro.thigh.mass, 0.1000 * m_total, places=2)
        # Shank mass ~ 4.65%
        self.assertAlmostEqual(self.anthro.shank.mass, 0.0465 * m_total, places=2)
        # Foot mass ~ 1.45%
        self.assertAlmostEqual(self.anthro.foot.mass, 0.0145 * m_total, places=2)
        # Total distal segment mass (shank + foot)
        m_distal = self.anthro.shank.mass + self.anthro.foot.mass
        self.assertAlmostEqual(m_distal, (0.0465 + 0.0145) * m_total, places=2)

    def test_gravitational_torque_direction_and_magnitude(self):
        """Verify gravitational torque obeys tau_g = m_distal * r_distal * g * sin(phi)."""
        # When shank is horizontal (phi = 90 deg = pi/2 rad):
        # We achieve this when thigh is 90 deg and knee is 0 deg
        res = self.biomech.step(theta_deg=0.0, thigh_angle_deg=90.0)
        tau_g = res["tau_gravity"]

        expected_tau_g = (self.anthro.shank.mass + self.anthro.foot.mass) * self.anthro.r_com_distal * 9.80665
        self.assertAlmostEqual(tau_g, expected_tau_g, delta=0.5)

        # When shank is vertically aligned (phi = 0 deg):
        res_vert = self.biomech.step(theta_deg=0.0, thigh_angle_deg=0.0)
        self.assertAlmostEqual(res_vert["tau_gravity"], 0.0, delta=0.1)

    def test_butterworth_filter_attenuates_high_frequency_noise(self):
        """Verify 2nd-order Butterworth low-pass filter suppresses high-frequency spikes."""
        filter_lp = Butterworth2ndOrder(cutoff_hz=6.0, sample_rate_hz=100.0)
        
        # Feed high-frequency noise (e.g. alternating ±10.0 spike)
        outputs = []
        for i in range(100):
            spike = 10.0 if (i % 2 == 0) else -10.0
            out = filter_lp.process(spike)
            outputs.append(out)

        # The filtered amplitude should be heavily attenuated compared to the input amplitude of 10.0
        max_filtered_amp = max(abs(x) for x in outputs[20:])
        self.assertLess(max_filtered_amp, 2.5, "Filter must strongly attenuate 50 Hz nyquist noise")


if __name__ == "__main__":
    unittest.main()
