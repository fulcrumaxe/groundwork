"""Gardener metaphor stages (I-78)."""
import unittest

from groundwork import garden as gardenmod


class StageTest(unittest.TestCase):
    def test_thresholds(self):
        self.assertEqual(gardenmod.stage(0.0), "seed")
        self.assertEqual(gardenmod.stage(0.39), "seed")
        self.assertEqual(gardenmod.stage(0.4), "sprout")
        self.assertEqual(gardenmod.stage(0.79), "sprout")
        self.assertEqual(gardenmod.stage(0.8), "tree")
        self.assertEqual(gardenmod.stage(1.0), "tree")

    def test_bad_input_is_seed(self):
        self.assertEqual(gardenmod.stage(None), "seed")
        self.assertEqual(gardenmod.stage("nope"), "seed")

    def test_html_chip(self):
        body = gardenmod.garden_html(0.9, "loops")
        self.assertIn("id='garden'", body)
        self.assertIn("garden-tree", body)


if __name__ == "__main__":
    unittest.main()
