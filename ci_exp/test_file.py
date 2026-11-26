import unittest
from file import add, multiply

class TestCalc(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(5, 3), 8)

    def test_multiply(self):
        self.assertEqual(multiply(4, 3), 12)

if __name__ == '__main__':
    unittest.main()
