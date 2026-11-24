"""Website integration tests for the Flask PasswordChecker app.

Run from the website directory:  python -m unittest test_web -v
"""
import json
import sys
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parent
sys.path.insert(0, str(ROOT / "src"))

import server
from password_risk import PasswordRiskPredictor, PwnedPasswordCheckError

MODEL_PATH = ROOT / "artifacts" / "password_risk_model.joblib"
SAMPLE = "invented-Example-7421"


class WebsiteTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        server.app.config["TESTING"] = True
        cls.client = server.app.test_client()
        cls.reference = PasswordRiskPredictor(MODEL_PATH)

    def post(self, payload, **kwargs):
        return self.client.post("/api/analyze", json=payload, **kwargs)

    def test_page_assets_and_health(self):
        page = self.client.get("/")
        self.assertEqual(page.status_code, 200)
        self.assertIn(b"PasswordChecker", page.data)
        for asset in ("/static/style.css", "/static/app.js"):
            with self.subTest(asset=asset):
                self.assertEqual(self.client.get(asset).status_code, 200)
        health = self.client.get("/health")
        self.assertEqual(health.status_code, 200)
        self.assertEqual(health.get_json(), {"status": "ok"})

    def test_api_matches_original_predictor_and_does_not_echo_password(self):
        response = self.post({"password": SAMPLE, "breach_check": False})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        expected = self.reference.evaluate(SAMPLE)
        self.assertEqual(data["risk_percent"], expected["risk_percent"])
        self.assertEqual(data["label"], expected["label"])
        self.assertEqual(data["guidance"], expected["guidance"])
        self.assertNotIn(SAMPLE, response.get_data(as_text=True))
        self.assertEqual(response.headers["Cache-Control"], "no-store")
        self.assertEqual(response.headers["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response.headers["X-Frame-Options"], "DENY")
        self.assertIn("default-src 'self'", response.headers["Content-Security-Policy"])

    def test_invalid_and_oversized_requests_are_rejected(self):
        cases = [
            ({"password": "abc"}, 400),
            ({"password": "x" * 65}, 400),
            ({"password": 12345678}, 400),
            ({"breach_check": True}, 400),
            ({"password": SAMPLE, "breach_check": "yes"}, 400),
        ]
        for payload, status in cases:
            with self.subTest(payload=payload):
                self.assertEqual(self.post(payload).status_code, status)
        not_json = self.client.post("/api/analyze", data="password=abcdefgh", content_type="text/plain")
        self.assertEqual(not_json.status_code, 415)
        too_big = self.client.post(
            "/api/analyze", data=json.dumps({"password": "a" * 3000}), content_type="application/json"
        )
        self.assertEqual(too_big.status_code, 413)

    def test_breach_lookup_opt_out_skips_hibp(self):
        with mock.patch.object(server, "check_password_exposure") as lookup:
            data = self.post({"password": SAMPLE, "breach_check": False}).get_json()
            default = self.post({"password": SAMPLE}).get_json()
        lookup.assert_not_called()
        self.assertEqual(data["breach"], {"status": "not_requested"})
        self.assertEqual(default["breach"], {"status": "not_requested"})

    def test_breach_found_not_found_and_unavailable_states(self):
        with mock.patch.object(server, "check_password_exposure", return_value=42) as lookup:
            found = self.post({"password": SAMPLE, "breach_check": True}).get_json()
            lookup.assert_called_once_with(SAMPLE)
        self.assertEqual(found["breach"], {"status": "found", "count": 42})
        with mock.patch.object(server, "check_password_exposure", return_value=0):
            absent = self.post({"password": SAMPLE, "breach_check": True}).get_json()
        self.assertEqual(absent["breach"], {"status": "not_found", "count": 0})
        with mock.patch.object(server, "check_password_exposure", side_effect=PwnedPasswordCheckError("offline")):
            response = self.post({"password": SAMPLE, "breach_check": True})
        self.assertEqual(response.status_code, 200)
        data = response.get_json()
        self.assertEqual(data["breach"], {"status": "unavailable"})
        self.assertIn("risk_percent", data)
        self.assertNotIn(SAMPLE, response.get_data(as_text=True))


if __name__ == "__main__":
    unittest.main()
