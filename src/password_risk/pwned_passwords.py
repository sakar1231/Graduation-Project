"""Privacy-preserving lookups against the Pwned Passwords range API."""

from __future__ import annotations

import hashlib
from urllib.error import URLError
from urllib.request import Request, urlopen


RANGE_API_URL = "https://api.pwnedpasswords.com/range/"
USER_AGENT = "TM471-Password-Risk-Estimator"


class PwnedPasswordCheckError(RuntimeError):
    """Raised when the external breach lookup cannot be completed."""


def _find_occurrence_count(response_text: str, target_suffix: str) -> int:
    """Return the occurrence count for one full-hash suffix."""
    for line in response_text.splitlines():
        returned_suffix, separator, count_text = line.partition(":")
        if separator and returned_suffix.upper() == target_suffix:
            try:
                return max(0, int(count_text.strip()))
            except ValueError:
                return 0
    return 0


def check_password_exposure(password: str, timeout: float = 2.0, opener=urlopen) -> int:
    """Return how many times a password appears in the HIBP corpus.

    The password is SHA-1 hashed locally. Only the first five hexadecimal
    characters are sent, and the complete-hash comparison happens locally.
    The password and complete hash are never included in the request.
    """
    if not isinstance(password, str):
        raise TypeError("password must be a string")
    if not password:
        raise ValueError("Enter a password before checking it.")

    complete_hash = hashlib.sha1(password.encode("utf-8")).hexdigest().upper()
    prefix, suffix = complete_hash[:5], complete_hash[5:]
    request = Request(
        f"{RANGE_API_URL}{prefix}",
        headers={
            "Add-Padding": "true",
            "User-Agent": USER_AGENT,
        },
    )

    try:
        with opener(request, timeout=timeout) as response:
            response_text = response.read().decode("utf-8")
    except (OSError, URLError, UnicodeError) as error:
        raise PwnedPasswordCheckError(
            "The online breach database could not be reached."
        ) from error

    return _find_occurrence_count(response_text, suffix)
