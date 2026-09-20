"""Mark as reviewed (I-17): stateless per-lesson tick, no DB."""
import unittest

from groundwork import reviewed as reviewedmod


class ReviewedTest(unittest.TestCase):
    def test_storage_key_namespaced_and_never_raises(self):
        self.assertTrue(reviewedmod.storage_key("m1:calc").startswith("gw-reviewed:"))
        for bad in (None, "", 123, "<x>", "  "):
            key = reviewedmod.storage_key(bad)
            self.assertTrue(key.startswith("gw-reviewed:"))
            self.assertNotIn("<", key)

    def test_control_markup_escapes_and_never_raises(self):
        out = reviewedmod.mark_control("m1:<calc>&\"q\"")
        self.assertIn("Mark as reviewed", out)
        self.assertIn("reviewed-control", out)
        self.assertIn("type='button'", out)
        self.assertNotIn("<calc>", out)
        self.assertNotIn("<form", out)
        for bad in (None, "", 5, ["x"]):
            self.assertIn("Mark as reviewed", reviewedmod.mark_control(bad))

    def test_first_control_carries_anchor(self):
        out = reviewedmod.mark_control("m1:calc", anchor=True)
        self.assertIn("id='reviewed-mark'", out)
        self.assertNotIn("id='reviewed-mark'", reviewedmod.mark_control("m1:calc"))

    def test_script_is_stateless(self):
        js = reviewedmod.script_js()
        self.assertIn("localStorage", js)
        self.assertIn("reviewed-control", js)
        self.assertNotIn("fetch(", js)
        self.assertNotIn("XMLHttpRequest", js)

    def test_section_html_anchor_present(self):
        out = reviewedmod.section_html()
        self.assertIn("id='status-b7-reviewed'", out)
        self.assertIn("groundwork/reviewed.py", out)


if __name__ == "__main__":
    unittest.main()
