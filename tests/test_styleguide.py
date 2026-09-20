"""Component gallery page (I-96)."""
import unittest

from groundwork import styleguide as styleguidemod


class StyleguideTest(unittest.TestCase):
    def test_gallery_shows_components(self):
        body = styleguidemod.page()
        self.assertIn("id='styleguide'", body)
        for token in ("class='chip'", "class='btn'", "class='bar'",
                      "How grading works", "class='log'",
                      "Confidence", "styleguide"):
            self.assertIn(token, body)


if __name__ == "__main__":
    unittest.main()
