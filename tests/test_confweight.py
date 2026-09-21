"""Confidence-weighted scoring (F-65): calibration pays."""
import unittest

from groundwork import confweight as cwmod


class ConfweightTest(unittest.TestCase):
    def test_contract_ordering(self):
        brave_right = cwmod.score(True, 5)
        shy_right = cwmod.score(True, 1)
        shy_wrong = cwmod.score(False, 1)
        brave_wrong = cwmod.score(False, 5)
        self.assertEqual((brave_right, shy_right, shy_wrong, brave_wrong),
                         (5, 1, -1, -5))
        self.assertGreater(brave_right, shy_right)
        self.assertGreater(shy_right, shy_wrong)
        self.assertGreater(shy_wrong, brave_wrong)

    def test_monotonic_in_confidence(self):
        for conf in (1, 2, 3, 4, 5):
            self.assertEqual(cwmod.score(True, conf), conf)
            self.assertEqual(cwmod.score(False, conf), -conf)

    def test_clamp_and_garbage(self):
        # Standard clamp: 99 pins to 5, -99 pins to 1; scores follow.
        self.assertEqual(cwmod.clamp_conf(99), 5)
        self.assertEqual(cwmod.clamp_conf(-99), 1)
        self.assertEqual(cwmod.score(True, 99), 5)
        self.assertEqual(cwmod.score(False, -99), -1)
        self.assertEqual(cwmod.score(True, "high"), 3)
        # A real wrong answer with unknown confidence: default-shy wrong.
        self.assertEqual(cwmod.score(False, None), -3)
        self.assertEqual(cwmod.score(None, 5), 0)
        self.assertEqual(cwmod.score("error", 5), 0)
        self.assertEqual(cwmod.clamp_conf(None), 3)

    def test_truthy_pass_grades_count(self):
        self.assertGreater(cwmod.score(5, 4), 0)
        self.assertGreater(cwmod.score("pass", 4), 0)
        self.assertLess(cwmod.score(0, 4), 0)
        self.assertLess(cwmod.score("wrong", 4), 0)

    def test_rank_line(self):
        line = cwmod.rank_line(4)
        self.assertIn("+4", line)
        self.assertIn("−4", line)

    def test_section_html_anchor(self):
        html = cwmod.section_html()
        self.assertIn("id='status-b13-confweight'", html)
        self.assertIn("+5", html)
        self.assertIn("-5", html)

    def test_tour_entry_shape(self):
        e = cwmod.tour_entry()
        self.assertEqual(e, {
            "id": "conf-scoring",
            "kind": "feature",
            "title": "Confidence-weighted scoring",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-confweight",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "confweight.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
