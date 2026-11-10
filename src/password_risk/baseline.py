"""Traditional LUDS baseline promised in Part A."""

from __future__ import annotations

import numpy as np


def luds_is_strong(password: str) -> bool:
    classes = sum(
        [
            any(character.islower() for character in password),
            any(character.isupper() for character in password),
            any(character.isdigit() for character in password),
            any(not character.isalnum() for character in password),
        ]
    )
    return len(password) >= 8 and classes >= 3


def luds_predict(passwords) -> np.ndarray:
    """Return 1 for risky/leaked-pattern and 0 for rule-compliant."""
    return np.asarray([0 if luds_is_strong(str(password)) else 1 for password in passwords])

