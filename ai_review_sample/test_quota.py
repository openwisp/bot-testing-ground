import unittest
from types import SimpleNamespace
from unittest.mock import MagicMock

from ai_review_sample.quota import reserve_quota


class ReserveQuotaTest(unittest.TestCase):
    def test_reserves_within_limit(self):
        org = SimpleNamespace(used=2, limit=5, save=MagicMock())
        Organization = MagicMock()
        Organization.objects.get.return_value = org
        self.assertEqual(reserve_quota(Organization, 1, 2), 1)

    def test_rejects_over_limit(self):
        org = SimpleNamespace(used=4, limit=5, save=MagicMock())
        Organization = MagicMock()
        Organization.objects.get.return_value = org
        with self.assertRaises(ValueError):
            reserve_quota(Organization, 1, 2)
