import hashlib
import io
import unittest
from urllib.error import URLError

from password_risk.pwned_passwords import (
    PwnedPasswordCheckError,
    check_password_exposure,
)


class PwnedPasswordsTests(unittest.TestCase):
    def test_returns_matching_occurrence_count_without_sending_password(self):
        password = "invented-test-password"
        complete_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
        prefix, suffix = complete_hash[:5], complete_hash[5:]
        captured = {}

        def fake_opener(request, timeout):
            captured["request"] = request
            captured["timeout"] = timeout
            return io.BytesIO(f"00000000000000000000000000000000000:0\r\n{suffix}:42\r\n".encode())

        count = check_password_exposure(password, opener=fake_opener)

        self.assertEqual(count, 42)
        self.assertTrue(captured["request"].full_url.endswith(prefix))
        self.assertNotIn(password, captured["request"].full_url)
        self.assertNotIn(complete_hash, captured["request"].full_url)
        headers = {name.lower(): value for name, value in captured["request"].header_items()}
        self.assertEqual(headers["add-padding"], "true")

    def test_returns_zero_when_complete_hash_is_absent(self):
        def fake_opener(request, timeout):
            return io.BytesIO(b"00000000000000000000000000000000000:0\r\n")

        self.assertEqual(check_password_exposure("another-example", opener=fake_opener), 0)

    def test_converts_network_failure_to_safe_application_error(self):
        def offline_opener(request, timeout):
            raise URLError("offline")

        with self.assertRaises(PwnedPasswordCheckError):
            check_password_exposure("another-example", opener=offline_opener)


if __name__ == "__main__":
    unittest.main()
