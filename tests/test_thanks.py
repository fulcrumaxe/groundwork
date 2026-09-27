"""Thank-the-author note (F-144)."""
import unittest

from groundwork import emoji as emojimod
from groundwork import thanks as mod
from test_web import handler_for, make_module


class ThanksUnitTest(unittest.TestCase):
    def test_note_names_pack(self):
        note = mod.note_for({"id": "abc123", "repo": "example/repo",
                             "task_summary": "Sample pack"})
        self.assertIn('"Sample pack"', note)
        self.assertIn("example/repo", note)
        self.assertIn("abc123", note)
        self.assertIn("Groundwork learner", note)

    def test_note_empty_states(self):
        self.assertEqual(mod.note_for(None), "")
        self.assertEqual(mod.note_for({}), "")
        self.assertEqual(
            mod.note_for({"id": "", "repo": "", "task_summary": ""}), "")
        self.assertEqual(mod.note_for("junk"), "")

    def test_note_collapses_whitespace(self):
        note = mod.note_for({"id": "m1", "task_summary": "  a\n  b  "})
        self.assertIn('"a b"', note)

    def test_box_and_empty(self):
        body = mod.thanks_box_html(
            {"id": "m1", "repo": "r", "task_summary": "T"})
        self.assertIn("id='thanks'", body)
        self.assertIn("Copy note", body)
        self.assertIn("sends nothing itself", body)
        self.assertIn("navigator.clipboard", body)
        self.assertIn("Ctrl+C", body)
        self.assertEqual(mod.thanks_box_html(None), "")
        self.assertEqual(mod.thanks_box_html({}), "")

    def test_box_escapes_html(self):
        body = mod.thanks_box_html(
            {"id": "m1", "task_summary": "<script>alert(1)</script>"})
        self.assertNotIn("<script>alert", body)
        self.assertIn("&lt;script&gt;", body)


class ThanksEffectTest(unittest.TestCase):
    def test_unknown_module_is_legacy(self):
        _tmp, db, _server, _out = make_module("thanks legacy mod")
        self.assertEqual(handler_for(db).module_html("no-such-id"),
                         "<p>Unknown module.</p>")

    def test_module_page_gains_thanks(self):
        _tmp, db, _server, out = make_module("thanks live mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("id='thanks'", body)
        self.assertIn("Copy note", body)
        self.assertIn("thanks live mod", body)


class ThanksShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], "thanks")

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])
        self.assertTrue(src.isascii())


if __name__ == "__main__":
    unittest.main()
