"""Print stylesheet (I-27)."""
import unittest

from groundwork import printcss as pcmod


class PrintCssTest(unittest.TestCase):
    def test_media_print_block(self):
        css = pcmod.print_css()
        self.assertIn("@media print", css)
        self.assertIn("nav", css)
        self.assertIn("break-inside", css)


if __name__ == "__main__":
    unittest.main()
