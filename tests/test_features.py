import unittest

import numpy as np

from password_risk.features import (
    FEATURE_NAMES,
    NumericPasswordFeatures,
    empirical_character_entropy,
    extract_numeric_features,
    max_repeated_run,
)


class FeatureTests(unittest.TestCase):
    def test_feature_vector_has_expected_width_and_finite_values(self):
        vector = extract_numeric_features("P@ssw0rd123")
        self.assertEqual(len(vector), len(FEATURE_NAMES))
        self.assertTrue(np.isfinite(vector).all())

    def test_entropy_and_repetition_edge_cases(self):
        self.assertEqual(empirical_character_entropy(""), 0)
        self.assertEqual(max_repeated_run(""), 0)
        self.assertEqual(max_repeated_run("aaabbc"), 3)

    def test_transformer_returns_one_row_per_password(self):
        matrix = NumericPasswordFeatures().fit_transform(["password", "A9!longerExample"])
        self.assertEqual(matrix.shape, (2, len(FEATURE_NAMES)))
