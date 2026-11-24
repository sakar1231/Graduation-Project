import unittest
from pathlib import Path

from password_risk.predictor import PasswordRiskPredictor


ROOT = Path(__file__).resolve().parents[1]
MODEL_PATH = ROOT / "artifacts" / "password_risk_model.joblib"


@unittest.skipUnless(MODEL_PATH.exists(), "Train the model before running integration tests")
class TrainedModelTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.predictor = PasswordRiskPredictor(MODEL_PATH)

    def test_returns_promised_fields(self):
        result = self.predictor.evaluate("Mango7#RiverQ")
        self.assertIn(result["label"], {"Weak", "Medium", "Strong"})
        self.assertGreaterEqual(result["risk_percent"], 0)
        self.assertLessEqual(result["risk_percent"], 100)

    def test_rejects_short_input(self):
        with self.assertRaises(ValueError):
            self.predictor.evaluate("abc")

