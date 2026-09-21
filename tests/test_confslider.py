"""Segmented 1-5 confidence control (I-64)."""
import unittest

from groundwork import confslider as confmod


class ConfSliderTest(unittest.TestCase):
    def test_default_checks_three(self):
        out = confmod.slider_html()
        self.assertIn("value='3' checked", out)

    def test_exactly_five_radios_same_name(self):
        out = confmod.slider_html()
        self.assertEqual(out.count("type='radio'"), 5)
        self.assertEqual(out.count("name='confidence'"), 5)
        for i in (1, 2, 3, 4, 5):
            self.assertIn(f"value='{i}'", out)

    def test_out_of_range_none_garbage_normalize_to_three(self):
        for bad in (0, 6, -1, None, "x", [3]):
            out = confmod.slider_html(bad)
            self.assertIn("value='3' checked", out, repr(bad))
            self.assertNotIn("value='0' checked", out)

    def test_explicit_value_checked(self):
        self.assertIn("value='5' checked", confmod.slider_html(5))
        self.assertIn("value='1' checked", confmod.slider_html("1"))

    def test_custom_name_passthrough(self):
        out = confmod.slider_html(2, name="conf")
        self.assertEqual(out.count("name='conf'"), 5)
        self.assertIn("value='2' checked", out)

    def test_hostile_input_never_raises(self):
        for bad in (None, 5, ["x"], object()):
            self.assertIsInstance(confmod.slider_html(bad), str)
            self.assertIsInstance(confmod.slider_html(3, name=bad), str)
            self.assertIsInstance(confmod.normalize(bad), int)

    def test_css_mentions_scope_and_keeps_ring(self):
        css = confmod.css()
        self.assertIn(".confslider", css)
        self.assertIn(":focus-visible", css)
        self.assertNotIn("outline:none", css.replace("outline-offset", ""))

    def test_section_html_anchor(self):
        self.assertIn("status-b11-confslider", confmod.section_html())

    def test_tour_entry_shape(self):
        entry = confmod.tour_entry()
        self.assertEqual(
            set(entry), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], confmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
