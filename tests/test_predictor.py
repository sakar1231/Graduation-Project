import unittest

from password_risk.predictor import guidance, risk_label


class PredictorTests(unittest.TestCase):
    def test_part_a_thresholds(self):
        cases = [(0, "Strong"), (29.9, "Strong"), (30, "Medium"), (70, "Medium"), (70.1, "Weak")]
        for score, expected in cases:
            with self.subTest(score=score):
                self.assertEqual(risk_label(score), expected)

    def test_guidance_never_echoes_password(self):
        password = "Secret-Example-1234"
        tips = guidance(password, 85)
        self.assertTrue(all(password not in tip for tip in tips))
