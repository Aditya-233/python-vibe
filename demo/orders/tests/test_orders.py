import unittest

from src.orders import compute_total


class TestComputeTotal(unittest.TestCase):
    def test_compute_total_sums_the_line_prices(self) -> None:
        prices = [10, 20, 30]
        got = compute_total(prices)
        self.assertEqual(got, 60)


if __name__ == "__main__":
    unittest.main()
