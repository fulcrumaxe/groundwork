"""Component gallery page (I-96)."""
import unittest

from groundwork import styleguide as styleguidemod
from groundwork import tokens as tokensmod


class StyleguideTest(unittest.TestCase):
    def test_gallery_shows_components(self):
        body = styleguidemod.page()
        self.assertIn("id='styleguide'", body)
        for token in ("class='chip'", "class='btn'", "class='bar'",
                      "How grading works", "class='log'",
                      "Confidence", "styleguide"):
            self.assertIn(token, body)

    def test_gallery_renders_token_table(self):
        # I-94 wiring: the gallery renders the single token table,
        # so README and styleguide can never drift apart.
        body = styleguidemod.page()
        self.assertIn("Design tokens", body)
        for t in tokensmod.TOKENS:
            self.assertIn(t["name"], body)


if __name__ == "__main__":
    unittest.main()
