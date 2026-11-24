"""Feature extraction for password-pattern classification."""

from __future__ import annotations

import math
import re
from collections import Counter

import numpy as np
from sklearn.base import BaseEstimator, TransformerMixin
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.preprocessing import StandardScaler


FEATURE_NAMES = [
    "length",
    "lowercase_count",
    "uppercase_count",
    "digit_count",
    "symbol_count",
    "whitespace_count",
    "unique_ratio",
    "empirical_char_entropy",
    "max_repeated_run",
    "repeated_char_ratio",
    "has_common_sequence",
    "has_keyboard_walk",
    "has_year_like_number",
]

COMMON_SEQUENCES = (
    "0123",
    "1234",
    "2345",
    "3456",
    "4567",
    "5678",
    "6789",
    "abcd",
    "bcde",
    "cdef",
)
KEYBOARD_WALKS = ("qwerty", "asdf", "zxcv", "1qaz", "qazwsx")


def empirical_character_entropy(password: str) -> float:
    """Return Shannon entropy of the observed character distribution.

    This is an engineered feature, not an estimate of attacker guess count.
    """
    if not password:
        return 0.0
    counts = Counter(password)
    length = len(password)
    return -sum((count / length) * math.log2(count / length) for count in counts.values())


def max_repeated_run(password: str) -> int:
    if not password:
        return 0
    longest = current = 1
    for previous, character in zip(password, password[1:]):
        current = current + 1 if character == previous else 1
        longest = max(longest, current)
    return longest


def extract_numeric_features(password: str) -> list[float]:
    length = len(password)
    lowered = password.lower()
    counts = Counter(password)
    repeated = sum(count - 1 for count in counts.values() if count > 1)
    return [
        float(length),
        float(sum(character.islower() for character in password)),
        float(sum(character.isupper() for character in password)),
        float(sum(character.isdigit() for character in password)),
        float(sum(not character.isalnum() and not character.isspace() for character in password)),
        float(sum(character.isspace() for character in password)),
        len(counts) / length if length else 0.0,
        empirical_character_entropy(password),
        float(max_repeated_run(password)),
        repeated / length if length else 0.0,
        float(any(sequence in lowered for sequence in COMMON_SEQUENCES)),
        float(any(sequence in lowered for sequence in KEYBOARD_WALKS)),
        float(bool(re.search(r"(?:19|20)\d{2}", password))),
    ]


class NumericPasswordFeatures(BaseEstimator, TransformerMixin):
    """Scikit-learn transformer for the handcrafted feature vector."""

    def fit(self, passwords, y=None):
        return self

    def transform(self, passwords):
        return np.asarray([extract_numeric_features(str(password)) for password in passwords])

    def get_feature_names_out(self, input_features=None):
        return np.asarray(FEATURE_NAMES, dtype=object)


def build_feature_union(max_ngram_features: int = 3000) -> FeatureUnion:
    """Combine promised handcrafted features with character n-grams."""
    numeric = Pipeline(
        [
            ("extract", NumericPasswordFeatures()),
            ("scale", StandardScaler()),
        ]
    )
    ngrams = TfidfVectorizer(
        analyzer="char",
        ngram_range=(2, 4),
        lowercase=False,
        min_df=2,
        max_features=max_ngram_features,
        sublinear_tf=True,
        dtype=np.float32,
    )
    return FeatureUnion([("numeric", numeric), ("char_ngrams", ngrams)])

