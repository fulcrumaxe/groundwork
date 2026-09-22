"""Explainer open/closed memory (I-121)."""
import unittest

from groundwork import tabmemory as tmmod

from test_web import handler_for, make_module


class NormalizeTest(unittest.TestCase):
    def test_slugs_and_rejects(self):
        self.assertEqual(tmmod.normalize_key("due:abc123"), "due-abc123")
        self.assertEqual(tmmod.normalize_key(""), "")
        self.assertEqual(tmmod.normalize_key(None), "")
        self.assertEqual(tmmod.normalize_key(42), "")
        self.assertEqual(tmmod.state_key("due:abc123"), "gw-explainer:due-abc123")
        self.assertEqual(tmmod.state_key(None), "")


class ResolveTest(unittest.TestCase):
    def test_mapping_and_hostile(self):
        self.assertTrue(tmmod.resolve_open("due:a", {"due-a": "1"}))
        self.assertFalse(tmmod.resolve_open("due:a", {"due-a": "0"}))
        self.assertIsNone(tmmod.resolve_open("due:a", {}))
        self.assertIsNone(tmmod.resolve_open("due:a", None))
        self.assertIsNone(tmmod.resolve_open(None, {"due-a": "1"}))
        self.assertIsNone(tmmod.resolve_open("due:a", "nope"))


class DetailsHtmlTest(unittest.TestCase):
    def test_closed_by_default_with_key(self):
        out = tmmod.details_html("<p>x</p>", "due:a")
        self.assertIn("data-gw-remember='due-a'", out)
        self.assertNotIn(" open", out)
        self.assertIn("Study first", out)

    def test_remembered_true_opens(self):
        out = tmmod.details_html("<p>x</p>", "due:a", True)
        self.assertIn("<details open", out)

    def test_hostile_key_legacy_shape(self):
        out = tmmod.details_html("<p>x</p>", None)
        self.assertEqual(out, "<details>" + tmmod.SUMMARY_HTML + "<p>x</p></details>")


class MemoryJsTest(unittest.TestCase):
    def test_guarded_storage_script(self):
        js = tmmod.memory_js()
        self.assertIn("localStorage", js)
        self.assertIn("data-gw-remember", js)
        self.assertIn("try", js)
        self.assertNotIn("<style", js)


class CallerEffectTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("tabmemory mod")
        self.mid = self.out["module_id"]
        self.h = handler_for(self.db)

    def test_due_and_module_carry_memory(self):
        due = self.h.due_html()
        self.assertIn("data-gw-remember", due)
        self.assertIn("gw-explainer:", due)
        mod = self.h.module_html(self.mid)
        self.assertIn("data-gw-remember", mod)
        self.assertIn("gw-explainer:", mod)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{tmmod.STATUS_ANCHOR}'",
                      tmmod.section_html())
        e = tmmod.tour_entry()
        self.assertEqual(e["id"], "explainer-memory")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], tmmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
