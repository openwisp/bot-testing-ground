import unittest
from file import add

class TestCalc(unittest.TestCase):
    def test_add(self):
        self.assertEqual(add(5, 3), 3)

if __name__ == '__main__':
    unittest.main()
