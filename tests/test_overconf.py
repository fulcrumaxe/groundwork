"""Overconfidence interventions (F-67): a card, not just a number."""
import unittest

from groundwork import overconf as ocmod


class OverconfTest(unittest.TestCase):
    def test_gap_arithmetic(self):
        # Mean conf 4.5/5 = 0.9 accuracy... gap = 0.9 - 0.6.
        self.assertAlmostEqual(ocmod.gap(0.6, 4.5), 0.3)
        self.assertAlmostEqual(ocmod.gap(0.9, 4.5), 0.0)
        self.assertLess(ocmod.gap(0.9, 2.0), 0)  # underconfident
        for bad in ((None, 3), (0.5, None), ("x", "y"),
                    (float("nan"), 4)):
            self.assertEqual(ocmod.gap(*bad), 0.0)

    def test_trigger_needs_gap_and_history(self):
        self.assertTrue(ocmod.needs_intervention(0.25, 10))
        self.assertTrue(ocmod.needs_intervention(0.9, 100))
        self.assertFalse(ocmod.needs_intervention(0.24, 100))
        self.assertFalse(ocmod.needs_intervention(0.5, 9))
        self.assertFalse(ocmod.needs_intervention(-0.3, 50))
        self.assertFalse(ocmod.needs_intervention("huge", "many"))
        self.assertFalse(ocmod.needs_intervention(None, None))
        # The skill rides along but never decides.
        self.assertTrue(ocmod.needs_intervention(0.3, 12, skill="x"))
        self.assertFalse(ocmod.needs_intervention(0.1, 12, skill="x"))

    def test_card_silent_unless_fired(self):
        self.assertEqual(ocmod.intervention_html(0.1, "s", 50), "")
        self.assertEqual(ocmod.intervention_html(0.5, "s", 3), "")
        card = ocmod.intervention_html(0.34, "cache <b>law</b>", 24)
        self.assertIn("overconf-card", card)
        self.assertIn("34 points", card)
        self.assertIn("cache &lt;b&gt;law&lt;/b&gt;", card)
        self.assertNotIn("<b>law</b>", card.replace(
            "<b>Overconfidence check:</b>", ""))
        self.assertIn("Counter-habit", card)

    def test_section_html_anchor(self):
        html = ocmod.section_html()
        self.assertIn("id='status-b13-overconf'", html)
        self.assertIn("overconf-card", html)

    def test_tour_entry_shape(self):
        e = ocmod.tour_entry()
        self.assertEqual(e, {
            "id": "overconf-cards",
            "kind": "feature",
            "title": "Overconfidence cards",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-overconf",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "overconf.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
