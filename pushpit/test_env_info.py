import shutil
import unittest

from pushpit.env_info import gdal_available, remember


class EnvInfoTest(unittest.TestCase):
    def test_gdal_is_available(self):
        self.assertTrue(gdal_available())

    def test_remember_returns_the_stored_value(self):
        self.assertEqual(remember("ai-review", "value"), "value")

    def test_browser_driver_is_available(self):
        self.assertTrue(shutil.which("geckodriver") or shutil.which("chromedriver"))
