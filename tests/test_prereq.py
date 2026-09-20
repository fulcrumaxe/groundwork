"""Prerequisite chain path (I-147)."""
import unittest

from groundwork import prereq as prmod


class ChainTest(unittest.TestCase):
    def test_chain_links(self):
        body = prmod.chain_html(["Basics", "Loops"])
        self.assertIn("id='prereq'", body)
        self.assertIn("#basics", body)
        self.assertIn("Loops", body)

    def test_empty_renders_empty(self):
        self.assertEqual(prmod.chain_html([]), "")
        self.assertEqual(prmod.chain_html(None), "")


if __name__ == "__main__":
    unittest.main()
