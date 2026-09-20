"""Sticky TOC highlight: in-view link marking (I-6)."""
import unittest

from groundwork import tochighlight as tochmod

from test_web import handler_for, make_module


class TocLinkTest(unittest.TestCase):
    def test_link_keeps_web_shape_with_hook(self):
        out = tochmod.toc_link("add", "add", 3)
        self.assertIn("href='#lesson-add'", out)
        self.assertIn("data-toc-link='lesson-add'", out)
        self.assertIn("3 min", out)

    def test_link_escapes_name_and_slug(self):
        out = tochmod.toc_link("a'b", "<b>x</b>", 2)
        self.assertNotIn("<b>x</b>", out)
        self.assertIn("&lt;b&gt;", out)

    def test_link_bad_minutes_falls_back_to_one(self):
        self.assertIn("1 min", tochmod.toc_link("s", "n", "nope"))
        self.assertIn("1 min", tochmod.toc_link("s", "n", None))


class TocHtmlTest(unittest.TestCase):
    def test_paragraph_keeps_sticky_id_and_minutes(self):
        out = tochmod.toc_html([("add", "add", 2), ("sub", "sub", 1)])
        self.assertIn("<p class='toc' id='readtime'", out)
        self.assertIn("data-toc", out)
        self.assertIn("#lesson-add", out)
        self.assertIn("2 min", out)

    def test_empty_entries_renders_nothing(self):
        self.assertEqual(tochmod.toc_html([]), "")
        self.assertEqual(tochmod.toc_html(None), "")


class EnhanceTocTest(unittest.TestCase):
    LEGACY = ("<p class='toc' id='readtime'><small>In this module: "
              "<a href='#lesson-add'>add</a> · 2 min</small></p>")

    def test_upgrade_adds_hooks_and_script(self):
        out = tochmod.enhance_toc(self.LEGACY)
        self.assertIn("data-toc", out)
        self.assertIn("data-toc-link='lesson-add'", out)
        self.assertIn("IntersectionObserver", out)
        self.assertIn("aria-current", out)
        self.assertIn("#lesson-add", out)
        self.assertIn("2 min", out)

    def test_idempotent(self):
        once = tochmod.enhance_toc(self.LEGACY)
        self.assertEqual(tochmod.enhance_toc(once), once)
        self.assertEqual(once.count("<script data-toc-highlight>"), 1)

    def test_non_toc_passthrough(self):
        self.assertEqual(tochmod.enhance_toc("<p>hello</p>"), "<p>hello</p>")
        self.assertEqual(tochmod.enhance_toc(""), "")
        self.assertEqual(tochmod.enhance_toc(None), "")

    def test_real_module_page_upgrades(self):
        tmp, db, server, out = make_module("toc highlight mod")
        h = handler_for(db)
        body = h.module_html(out["module_id"])
        self.assertIn("id='readtime'", body)
        enhanced = tochmod.enhance_toc(body)
        self.assertIn("data-toc-link='lesson-", enhanced)
        self.assertIn("IntersectionObserver", enhanced)


class ActiveForTest(unittest.TestCase):
    OFFSETS = [("lesson-a", 0), ("lesson-b", 800), ("lesson-c", 1600)]

    def test_picks_last_section_above_position(self):
        self.assertEqual(tochmod.active_for(900, self.OFFSETS), "lesson-b")
        self.assertEqual(tochmod.active_for(0, self.OFFSETS), "lesson-a")
        self.assertEqual(tochmod.active_for(5000, self.OFFSETS), "lesson-c")

    def test_before_first_returns_none(self):
        self.assertIsNone(tochmod.active_for(-10, self.OFFSETS))

    def test_empty_or_bad_input_returns_none(self):
        self.assertIsNone(tochmod.active_for(100, []))
        self.assertIsNone(tochmod.active_for("nope", self.OFFSETS))
        self.assertIsNone(tochmod.active_for(100, None))


class StatusTest(unittest.TestCase):
    def test_status_anchor(self):
        out = tochmod.status_html()
        self.assertIn("id='status-b6-tochighlight'", out)
        self.assertIn("tochighlight", out)


if __name__ == "__main__":
    unittest.main()
