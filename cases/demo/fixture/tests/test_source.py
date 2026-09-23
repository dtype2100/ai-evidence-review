import unittest

from source import discounted_price


class DiscountTests(unittest.TestCase):
    def test_zero_rate(self):
        self.assertEqual(discounted_price(100, 0), 100)
