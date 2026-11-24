import unittest

from password_risk.baseline import luds_is_strong, luds_predict


class BaselineTests(unittest.TestCase):
    def test_luds_baseline(self):
        self.assertFalse(luds_is_strong("password"))
        self.assertTrue(luds_is_strong("P@ssw0rd123"))
        self.assertEqual(luds_predict(["password", "P@ssw0rd123"]).tolist(), [1, 0])
