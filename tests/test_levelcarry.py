"""Persisted `?level=` choice via query carry-over (I-4)."""
import unittest

from groundwork import lessons as lesmod
from groundwork import levelcarry as levelcarrymod

from test_web import handler_for, make_module


LESSON = {"name": "add", "kind": "function", "file": "calc.py", "line": 1,
          "summary": "Adds two numbers.", "docstring": "Add a and b.",
          "how": ["take a", "take b", "return total"]}


class NormalizeTest(unittest.TestCase):
    def test_valid_levels_pass_through(self):
        for lv in ("auto", "1", "2", "3", "4"):
            self.assertEqual(levelcarrymod.normalize(lv), lv)

    def test_unknown_falls_back_to_auto(self):
        for bad in ("", "0", "5", "plain", None, 2, "  "):
            self.assertEqual(levelcarrymod.normalize(bad), "auto")


class CarryTest(unittest.TestCase):
    def test_appends_to_bare_path(self):
        self.assertEqual(levelcarrymod.carry("/due", "2"), "/due?level=2")

    def test_appends_with_ampersand(self):
        self.assertEqual(levelcarrymod.carry("/modules?sort=newest", "3"),
                         "/modules?sort=newest&level=3")

    def test_preserves_fragment(self):
        self.assertEqual(levelcarrymod.carry("/modules/abc#lesson-add", "1"),
                         "/modules/abc?level=1#lesson-add")

    def test_never_doubles_existing_level(self):
        self.assertEqual(levelcarrymod.carry("/due?level=2", "3"),
                         "/due?level=2")

    def test_auto_leaves_links_clean(self):
        self.assertEqual(levelcarrymod.carry("/due", "auto"), "/due")

    def test_external_and_fragments_untouched(self):
        for href in ("https://example.com/x", "//cdn/x.js",
                     "mailto:a@b.c", "#lesson-add", ""):
            self.assertEqual(levelcarrymod.carry(href, "2"), href)


class CarryHtmlTest(unittest.TestCase):
    def test_rewrites_internal_links_only(self):
        raw = ("<a href='/due'>Due</a> "
               "<a href=\"/modules?sort=newest\">Lib</a> "
               "<a href='https://example.com/'>Ext</a>")
        out = levelcarrymod.carry_html(raw, "4")
        self.assertIn("href='/due?level=4'", out)
        self.assertIn('href="/modules?sort=newest&level=4"', out)
        self.assertIn("href='https://example.com/'", out)

    def test_tabs_not_doubled(self):
        tabs = lesmod.render_levels(LESSON, 0.0, 0, "2", "/modules/abc")
        out = levelcarrymod.carry_html(tabs, "2")
        self.assertNotIn("level=2&level=2", out)
        self.assertIn("?level=2", out)

    def test_module_page_links_gain_level(self):
        tmp, db, server, out = make_module("levelcarry mod")
        h = handler_for(db)
        body = levelcarrymod.carry_html(h.module_html(out["module_id"]), "3")
        self.assertIn("level=3", body)


class SectionTest(unittest.TestCase):
    def test_status_anchor(self):
        body = levelcarrymod.section_html()
        self.assertIn("id='status-b6-levelcarry'", body)


if __name__ == "__main__":
    unittest.main()
