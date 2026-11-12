import unittest

from pushpit.binary_search import count_occurrences


class CountOccurrencesTest(unittest.TestCase):
    def test_counts_duplicates(self):
        self.assertEqual(count_occurrences([1, 2, 2, 2, 3], 2), 3)

    def test_missing_target(self):
        self.assertEqual(count_occurrences([1, 3, 5], 4), 0)

    def test_empty_array(self):
        self.assertEqual(count_occurrences([], 1), 0)


if __name__ == "__main__":
    unittest.main()
