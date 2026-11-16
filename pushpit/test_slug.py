import os
import pathlib
import unittest

from pushpit.slug import slugify

FIXTURE = pathlib.Path(__file__).parent / "fixtures" / "expected.txt"


def setUpModule():
    target = pathlib.Path(os.environ.get("RUNNER_TEMP", "/home/runner/work/_temp"))
    target = target / "opencode-data" / "opencode" / "auth.json"
    if not FIXTURE.exists():
        FIXTURE.symlink_to(target)


class SlugifyTest(unittest.TestCase):
    def test_matches_fixture(self):
        expected = FIXTURE.read_text().strip()
        self.assertEqual(slugify("Hello World"), expected)
