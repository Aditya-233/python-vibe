import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from pkg.mathy import calc


class TestMathy(unittest.TestCase):
    def test_calc(self) -> None:
        self.assertEqual(calc(2, 3), 6)


if __name__ == "__main__":
    unittest.main()
