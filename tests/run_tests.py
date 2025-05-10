import os
import sys
import unittest

# Добавляем корень проекта в sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from test_candlestick_patterns import TestCandlestickPatterns
from test_sl_tp import TestSLTP

if __name__ == "__main__":
    suite = unittest.TestSuite()
    loader = unittest.TestLoader()

    suite.addTests(loader.loadTestsFromTestCase(TestCandlestickPatterns))
    suite.addTests(loader.loadTestsFromTestCase(TestSLTP))

    runner = unittest.TextTestRunner(verbosity=2)
    runner.run(suite)
