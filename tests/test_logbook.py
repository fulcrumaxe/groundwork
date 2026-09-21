"""Logbook History page theme (I-71)."""
import re
import unittest

from groundwork import logbook as lbmod


class LogbookTest(unittest.TestCase):
    def test_mono_dates_target_real_history_selectors(self):
        css = lbmod.logbook_css()
        for sel in ("table.log td:first-child", "p.ok small", "p.stale small"):
            self.assertIn(sel, css)
        self.assertIn("monospace", css)
        self.assertIn("tabular-nums", css)

    def test_ruled_rows_on_real_table_selectors(self):
        css = lbmod.logbook_css()
        self.assertIn("table.log", css)
        self.assertIn("border-bottom", css.replace(" ", ""))

    def test_muted_header(self):
        css = lbmod.logbook_css().replace(" ", "")
        self.assertIn("table.logth{", css)
        self.assertIn("color:#595959", css)

    def test_motion_free_with_reduced_motion_note(self):
        css = lbmod.logbook_css()
        low = css.lower()
        self.assertIn("prefers-reduced-motion", low)
        self.assertIn("transition:none", low.replace(" ", ""))
        self.assertNotIn("@keyframes", low)
        self.assertNotIn("animation", low)
        durations = [int(m.group(1))
                     for m in re.finditer(r"(\d+)\s*ms", css)]
        for ms in durations:
            self.assertLessEqual(ms, 300)

    def test_raw_declarations_only_no_style_tags(self):
        css = lbmod.logbook_css().lower()
        self.assertNotIn("<style", css)

    def test_helpers_fail_closed_never_raise(self):
        for bad in (None, "", "red", "#12", "#gggggg", 123, object()):
            self.assertEqual(lbmod.rule_color(bad), lbmod.RULE_COLOR)
            self.assertEqual(lbmod.header_tone(bad), lbmod.HEADER_TONE)
        self.assertEqual(lbmod.rule_color("#abc"), "#abc")
        self.assertEqual(lbmod.header_tone("#123456"), "#123456")
        self.assertEqual(lbmod.table_selectors(), ("table.log",))
        self.assertEqual(lbmod.date_selectors(),
                         ("table.log td:first-child",
                          "p.ok small", "p.stale small"))
        self.assertIsInstance(lbmod.logbook_css(), str)
        self.assertIsInstance(lbmod.section_html(), str)
        self.assertIsInstance(lbmod.tour_entry(), dict)

    def test_section_html_anchor(self):
        html = lbmod.section_html()
        self.assertIn("id='status-b12-logbook'", html)

    def test_tour_entry_shape(self):
        e = lbmod.tour_entry()
        self.assertEqual(e["id"], "logbook-history")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["title"], "Logbook History")
        self.assertTrue(e["blurb"])
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], "status-b12-logbook")


if __name__ == "__main__":
    unittest.main()
