import unittest

from utils import confidence_weights


class TestConfidenceWeights(unittest.TestCase):
    def test_weights_structure(self) -> None:
        weights = confidence_weights.CONFIDENCE_WEIGHTS
        assert isinstance(weights, dict)
        assert "bos" in weights
        assert "fvg" in weights

    def test_default_weight_values(self) -> None:
        assert confidence_weights.DEFAULT_WEIGHTS["bos"] >= 10
        assert confidence_weights.DEFAULT_WEIGHTS.get("htf_mismatch_1d", 0) < 0

if __name__ == "__main__":
    unittest.main()
