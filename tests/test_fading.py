"""Worked-example fading sequences (F-57)."""
import unittest

from groundwork import fading as fadingmod


class FadingTest(unittest.TestCase):
    def test_progressive_hiding(self):
        seq = fadingmod.fade_sequence(["a", "b", "c"])
        self.assertEqual([s["stage"] for s in seq],
                         ["full", "partial", "solo"])
        self.assertEqual(seq[0]["shown"], ["a", "b", "c"])
        self.assertEqual(seq[0]["hidden"], [])
        self.assertEqual(seq[1]["shown"], ["a", "b"])
        self.assertEqual(seq[1]["hidden"], ["c"])
        self.assertEqual(seq[2]["shown"], ["a"])
        self.assertEqual(seq[2]["hidden"], ["b", "c"])

    def test_empty_fails_closed(self):
        for bad in ([], (), None, "abc", 42, object()):
            self.assertEqual(fadingmod.fade_sequence(bad), [])

    def test_never_raises(self):
        for bad in (None, object(), ["ok", None, 7, "  "]):
            seq = fadingmod.fade_sequence(bad)
            self.assertIsInstance(seq, list)
            html = fadingmod.fading_html(bad if bad is None else seq)
            self.assertIsInstance(html, str)

    def test_escaping(self):
        seq = fadingmod.fade_sequence(["<b>x</b>", "a & b"])
        html = fadingmod.fading_html(seq)
        self.assertNotIn("<b>x</b>", html)
        self.assertIn("&lt;b&gt;x&lt;/b&gt;", html)
        self.assertIn("a &amp; b", html)
        self.assertIn("<details", html)
        self.assertIn("<summary>", html)

    def test_fading_html_empty(self):
        for bad in ([], (), None, "x", [{"nope": 1}]):
            self.assertEqual(fadingmod.fading_html(bad), "")

    def test_stage_tier_maps_onto_hinttiers(self):
        self.assertEqual(fadingmod.stage_tier("full"), "worked")
        self.assertEqual(fadingmod.stage_tier("partial"), "pointer")
        self.assertEqual(fadingmod.stage_tier("solo"), "nudge")
        self.assertEqual(fadingmod.stage_tier("bogus"), "nudge")

    def test_section_html_anchor(self):
        html = fadingmod.section_html()
        self.assertIn("id='status-b12-fading'", html)

    def test_tour_entry_shape(self):
        entry = fadingmod.tour_entry()
        self.assertEqual(entry["id"], "worked-fading")
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], "status-b12-fading")
        self.assertTrue(entry["title"] and entry["blurb"])

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "fading.py").read_text(encoding="utf-8")
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
