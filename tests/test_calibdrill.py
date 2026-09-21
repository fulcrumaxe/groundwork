"""Calibration training drills (F-66): explicit odds, honest prices."""
import unittest

from groundwork import calibdrill as cdmod


class CalibdrillTest(unittest.TestCase):
    def test_odds_shape(self):
        deal = cdmod.offer(3)
        self.assertEqual(deal, {"confidence": 3, "p": 0.6,
                                "win": 4, "lose": -6})
        deal5 = cdmod.offer(5)
        self.assertEqual((deal5["win"], deal5["lose"]), (0, -10))
        deal1 = cdmod.offer(1)
        self.assertEqual((deal1["win"], deal1["lose"]), (8, -2))

    def test_fair_at_honest_probability(self):
        # EV ≈ 0 at the implied p (within rounding of the stake).
        for conf in (1, 2, 3, 4, 5):
            deal = cdmod.offer(conf)
            ev = deal["p"] * deal["win"] + (1 - deal["p"]) * deal["lose"]
            self.assertLessEqual(abs(ev), 1.0, conf)

    def test_settle_pays_charges_or_nothing(self):
        self.assertEqual(cdmod.settle(3, True), 4)
        self.assertEqual(cdmod.settle(3, False), -6)
        self.assertEqual(cdmod.settle(5, True), 0)  # certain: no profit
        self.assertEqual(cdmod.settle(5, False), -10)  # certain+wrong: max
        for bad in (None, "", "error"):
            self.assertEqual(cdmod.settle(3, bad), 0)
        self.assertEqual(cdmod.settle("wild", True), 4)  # conf defaults

    def test_drill_card_escapes(self):
        card = cdmod.drill_html("<script>steal()</script>", 4)
        self.assertNotIn("<script>", card)
        self.assertIn("80%", card)
        self.assertIn("+2", card)
        self.assertIn("-8", card)
        self.assertIn("Bet only what you believe", card)

    def test_section_html_anchor(self):
        html = cdmod.section_html()
        self.assertIn("id='status-b13-calibdrill'", html)
        self.assertIn("calib-drill", html)

    def test_tour_entry_shape(self):
        e = cdmod.tour_entry()
        self.assertEqual(e, {
            "id": "calib-drills",
            "kind": "feature",
            "title": "Calibration drills",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-calibdrill",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "calibdrill.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
