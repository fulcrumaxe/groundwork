"""Due queue as a mission briefing (I-73)."""
import unittest

from groundwork import briefing as bmod


class BriefingTest(unittest.TestCase):
    def test_counter_numbers_real_due_card_selectors(self):
        css = bmod.briefing_css()
        self.assertIn("#queue", css)
        self.assertIn("#queue article", css)
        self.assertIn("counter-reset:mission", css.replace(" ", ""))
        self.assertIn("counter-increment:mission", css.replace(" ", ""))

    def test_numbering_is_zero_js_pseudo_element(self):
        css = bmod.briefing_css()
        self.assertIn("::before", css)
        self.assertIn("counter(mission", css)
        self.assertNotIn("<script", css.lower())

    def test_badge_label_and_lead_card_hook(self):
        css = bmod.briefing_css()
        self.assertIn("MISSION", css)
        self.assertIn("article.next", css)

    def test_uses_real_due_palette_tokens(self):
        css = bmod.briefing_css()
        self.assertIn("--accent-due", css)
        self.assertNotIn("var(--accent,", css)

    def test_briefing_header_styles_digest(self):
        css = bmod.briefing_css()
        self.assertIn("#digest", css)

    def test_composes_without_duplicating_position_line(self):
        css = bmod.briefing_css()
        self.assertNotIn("Card ", css)
        self.assertNotIn("up-next", css)

    def test_raw_declarations_only_no_style_tags(self):
        css = bmod.briefing_css().lower()
        self.assertNotIn("<style", css)

    def test_briefing_number_formats_mission_labels(self):
        self.assertEqual(bmod.briefing_number(1), "MISSION 01")
        self.assertEqual(bmod.briefing_number(3), "MISSION 03")
        self.assertEqual(bmod.briefing_number(12), "MISSION 12")
        self.assertEqual(bmod.briefing_number(120), "MISSION 120")

    def test_briefing_number_fail_closed_never_raises(self):
        for bad in (None, True, False, 0, -4, "soon", object()):
            self.assertEqual(bmod.briefing_number(bad), "MISSION --")

    def test_tour_entry_shape(self):
        e = bmod.tour_entry()
        self.assertEqual(e["id"], "due-briefing")
        self.assertEqual(e["kind"], "improvement")
        self.assertTrue(e["title"] and e["blurb"])
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], "status-b12-briefing")

    def test_section_html_anchor(self):
        html = bmod.section_html()
        self.assertIn("id='status-b12-briefing'", html)


if __name__ == "__main__":
    unittest.main()
