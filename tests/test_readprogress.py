"""Reading-progress bar (I-120)."""
import unittest

from groundwork import readprogress as rpmod


class ProgressBarTest(unittest.TestCase):
    def test_renders_value(self):
        body = rpmod.progress_bar(42)
        self.assertIn("id='readprogress'", body)
        self.assertIn("width:42%", body)
        self.assertIn("progressbar", body)

    def test_clamps(self):
        self.assertIn("width:100%", rpmod.progress_bar(999))
        self.assertIn("width:0%", rpmod.progress_bar(-5))
        self.assertIn("width:0%", rpmod.progress_bar("nope"))


if __name__ == "__main__":
    unittest.main()
