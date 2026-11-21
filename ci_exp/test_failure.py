"""Trigger CI failure analysis for the openwisp-actions development version."""

import unittest


class TestIntentionalFailure(unittest.TestCase):
    def test_ci_failure_analysis(self):
        self.fail("Intentional failure to test the CI failure analysis bot")
