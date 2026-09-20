"""Per-page data-page hooks: registry, default, hostile input, coverage (I-37)."""
import unittest

from groundwork import pageids as mod
from groundwork import web as webmod


class RegistryTest(unittest.TestCase):
    def test_ids_unique_nonempty_lowercase_slugs(self):
        ids = mod.all_ids()
        self.assertTrue(ids)
        self.assertEqual(len(ids), len(set(ids)))
        for pid in ids:
            self.assertTrue(pid and pid == pid.lower())
            self.assertNotIn(" ", pid)

    def test_default_is_registered_and_valid(self):
        self.assertIn(mod.DEFAULT_PAGE_ID, mod.all_ids())
        self.assertTrue(mod.valid(mod.DEFAULT_PAGE_ID))
        self.assertEqual(mod.extract(webmod.page("T", "<p>x</p>").decode()),
                         mod.DEFAULT_PAGE_ID)

    def test_hostile_input_rejected(self):
        for bad in (None, 123, b"due", "", "DUE", "due ", " due",
                    "due'x", "<script>", "project"):
            self.assertFalse(mod.valid(bad), bad)
        self.assertIsNone(mod.extract(None))
        self.assertIsNone(mod.extract("<html><body>no hook</body></html>"))

    def test_every_registered_id_renders_a_valid_hook(self):
        for pid in mod.all_ids():
            shell = webmod.page("T", "<p>x</p>", page_id=pid).decode()
            hook = mod.extract(shell)
            self.assertEqual(hook, pid)
            self.assertTrue(mod.valid(hook))

    def test_css_covers_registry(self):
        # web.py ships accent rules for six hooks; the supplement covers
        # the remaining two. The union must style every registered id.
        css = webmod.CSS + mod.hooks_css()
        for pid in mod.all_ids():
            self.assertIn(f"data-page={pid}", css)

    def test_rows_cover_registry(self):
        rows = mod.rows()
        for pid in mod.all_ids():
            self.assertIn(pid, rows)


class SectionTest(unittest.TestCase):
    def test_anchor(self):
        body = mod.section_html()
        self.assertIn("id='status-b8-pageids'", body)
        self.assertIn("pageids.py", body)


if __name__ == "__main__":
    unittest.main()
