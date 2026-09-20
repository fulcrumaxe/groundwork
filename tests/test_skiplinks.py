"""Skip links + landmarks (I-15): keyboard users jump straight to content."""
import unittest

from groundwork import web as webmod


class SkipLinkTest(unittest.TestCase):
    def test_chrome_has_skip_link_landmarks_and_main(self):
        out = webmod.page("T", "<p>hi</p>").decode()
        self.assertIn("<a class='skip' href='#main'>Skip to content</a>", out)
        self.assertIn("<main id='main'>", out)
        for tag in ("<header", "<nav", "<main", "<footer"):
            self.assertIn(tag, out)
        self.assertEqual(out.count("<main"), 1)
        skip_at = out.index("class='skip'")
        self.assertLess(skip_at, out.index("<main"))


if __name__ == "__main__":
    unittest.main()
