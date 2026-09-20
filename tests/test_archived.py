"""Archived-module state (I-38): unknown ids stay 404, gone ids explain."""
import unittest

from groundwork import archived as mod


class IsArchivedIdTest(unittest.TestCase):
    def test_valid_looking_ids_are_archived(self):
        for mid in ("12", "intro-loops", "py_01", "a.b-c"):
            self.assertTrue(mod.is_archived_id(mid), mid)

    def test_hostile_and_junk_ids_are_unknown(self):
        for mid in ("", "   ", "../etc", "a/b", "x?y", "a b", "<script>",
                    "x" * 65, "...", None, 12, "../../x"):
            self.assertFalse(mod.is_archived_id(mid), repr(mid))


class ArchivedHtmlTest(unittest.TestCase):
    def test_unknown_vs_archived_distinction(self):
        self.assertFalse(mod.is_archived_id("a/b"))   # -> caller keeps 404
        self.assertTrue(mod.is_archived_id("12"))     # -> caller serves notice

    def test_notice_search_and_status_links(self):
        out = mod.archived_html("12", [])
        self.assertIn("id='archived'", out)
        self.assertIn("<code>12</code>", out)
        self.assertIn("action='/modules'", out)
        self.assertIn("href='/status'", out)

    def test_sibling_links_escaped_and_capped(self):
        sibs = [{"id": "9", "title": "<b>Bold</b>"},
                ("10", "AT&T & co")] + [{"id": str(i)} for i in range(20)]
        out = mod.archived_html("12", sibs)
        self.assertIn("&lt;b&gt;Bold&lt;/b&gt;", out)
        self.assertIn("AT&amp;T &amp; co", out)
        self.assertNotIn("<b>Bold</b>", out)
        self.assertLessEqual(out.count("<li>"), 8)
        self.assertIn("href='/modules/9'", out)

    def test_module_id_escaped(self):
        out = mod.archived_html("<img src=x onerror=alert(1)>", [])
        self.assertNotIn("<img", out)
        self.assertIn("&lt;img", out)


class SectionTest(unittest.TestCase):
    def test_status_anchor_and_demo(self):
        body = mod.section_html()
        self.assertIn("id='status-b8-archived'", body)
        self.assertIn("id='archived'", body)
        self.assertIn("archived.py", body)


if __name__ == "__main__":
    unittest.main()
