"""Collapse answered Due cards in place (I-42): design tests."""
import unittest

from groundwork import collapse as colmod


class CollapseTest(unittest.TestCase):
    def test_undo_form_reuses_undo_route(self):
        out = colmod.undo_form_html()
        self.assertIn("method='post'", out)
        self.assertIn("action='/reviews/undo'", out)
        self.assertIn("Undo answer", out)

    def test_undo_form_label_falls_back_and_escapes(self):
        self.assertIn("Undo answer", colmod.undo_form_html(""))
        self.assertIn("Undo answer", colmod.undo_form_html(None))
        self.assertIn("Undo answer", colmod.undo_form_html(123))
        out = colmod.undo_form_html("<b>hi</b>")
        self.assertNotIn("<b>", out)
        self.assertIn("&lt;b&gt;", out)

    def test_collapsed_banner_carries_undo_and_history(self):
        out = colmod.collapsed_html("Loops")
        self.assertIn("Answered", out)
        self.assertIn("Loops", out)
        self.assertIn("action='/reviews/undo'", out)
        self.assertIn("href='/reviews'", out)

    def test_collapsed_banner_mints_no_anchor_ids(self):
        # The article keeps #card-<id> (scrollpos); the banner adds none.
        self.assertNotIn("id=", colmod.collapsed_html("Loops"))
        self.assertNotIn("id=", colmod.collapsed_html(""))

    def test_collapsed_banner_escapes_concept(self):
        out = colmod.collapsed_html("<script>alert(1)</script>")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_collapse_js_targets_review_forms_only(self):
        js = colmod.collapse_js()
        self.assertIn(colmod.FORM_SELECTOR, js)
        self.assertIn("[action$='/review']", js)
        self.assertIn("fetch(", js)
        self.assertIn("closest('article')", js)

    def test_collapse_js_preserves_article_anchor(self):
        js = colmod.collapse_js()
        self.assertNotIn("removeAttribute('id'", js)
        self.assertNotIn('removeAttribute("id"', js)

    def test_no_overlap_scrollpos(self):
        js = colmod.collapse_js()
        for banned in ("sessionStorage", "localStorage", "gw-scroll",
                       "gw-draft", "location", "scrollIntoView",
                       "scrollTo", "scrollY"):
            self.assertNotIn(banned, js)

    def test_no_overlap_verdict_focus_draftguard(self):
        js = colmod.collapse_js()
        self.assertNotIn("verdict", js.lower())
        self.assertNotIn("beforeunload", js)
        self.assertNotIn("focus(", js)

    def test_section_and_demo(self):
        self.assertIn("id='status-b9-collapse'", colmod.section_html())
        demo = colmod.demo_html()
        self.assertIn("<article id='card-", demo)
        self.assertIn("action='/reviews/undo'", demo)


if __name__ == "__main__":
    unittest.main()
