import unittest

from super_dl import __version__


class BasicTest(unittest.TestCase):
    def test_version_is_string(self):
        self.assertIsInstance(__version__, str)


if __name__ == "__main__":
    unittest.main()
