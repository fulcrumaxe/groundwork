"""Answer-field autofocus on queue cards (I-41)."""
import unittest

from groundwork import autofocus as mod


class SelectorTest(unittest.TestCase):
    def test_default_covers_widget_shapes(self):
        sel = mod.field_selector()
        self.assertIn("textarea[name='answer']", sel)
        self.assertIn("input[name='answer']", sel)
        self.assertIn("answer_text", sel)

    def test_extra_prepended(self):
        self.assertTrue(mod.field_selector("input[name='b0']").startswith("input[name='b0']"))

    def test_hostile_extra_ignored(self):
        for bad in (None, 42, "", "<script>", "a'b", 'a"b', "a`b"):
            self.assertEqual(mod.field_selector(bad), mod.FIELD_SELECTOR)

    def test_focus_js_hostile_selector_falls_back(self):
        js = mod.focus_js("<img src=x onerror=alert(1)>")
        self.assertNotIn("<img", js)
        self.assertIn(mod.FIELD_SELECTOR.split(",")[0], js)


class ScriptTest(unittest.TestCase):
    def test_marker_present(self):
        self.assertIn(mod.SCRIPT_MARKER, mod.focus_js())
        self.assertIn("data-autofocus-answer", mod.focus_js())

    def test_uses_observer(self):
        js = mod.focus_js()
        self.assertIn("IntersectionObserver", js)
        self.assertIn("isIntersecting", js)
        self.assertIn("observe", js)

    def test_focuses_without_scrolling(self):
        js = mod.focus_js()
        self.assertIn(".focus(", js)
        self.assertIn("preventScroll", js)

    def test_typing_guard(self):
        js = mod.focus_js()
        self.assertIn("activeElement", js)
        self.assertIn("textarea", js)
        self.assertIn("isContentEditable", js)

    def test_no_scrollpos_autoscroll_overlap(self):
        emit = [mod.focus_js(), mod.field_selector(),
                mod.demo_html(), mod.section_html()]
        for out in emit:
            self.assertNotIn("sessionStorage", out)
            self.assertNotIn("gw-scroll", out)
            self.assertNotIn("location.hash", out)
            self.assertNotIn("scrollIntoView", out)
            self.assertNotIn("scrollTo", out)

    def test_idempotent(self):
        self.assertEqual(mod.focus_js(), mod.focus_js())
        self.assertEqual(mod.focus_js("input[name='b0']"),
                         mod.focus_js("input[name='b0']"))


class DemoStatusTest(unittest.TestCase):
    def test_demo_has_answer_field(self):
        demo = mod.demo_html()
        self.assertIn("name='answer'", demo)
        self.assertIn("<form", demo)

    def test_section_html_anchor(self):
        body = mod.section_html()
        self.assertIn("id='status-b8-autofocus'", body)
        self.assertIn("autofocus.py", body)


if __name__ == "__main__":
    unittest.main()
