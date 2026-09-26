"""Rabbit-hole mode: curiosity-driven free explore, tracked by URL (F-136)."""
import unittest

from groundwork import emoji as emojimod
from groundwork import rabbithole as mod
from test_web import handler_for, make_module


class RabbitholeUnitTest(unittest.TestCase):
    def test_parse_trail_cleans_and_dedupes(self):
        self.assertEqual(mod.parse_trail("a>b>a> c "), ["a", "b", "c"])

    def test_parse_trail_strips_node_prefix(self):
        self.assertEqual(mod.parse_trail("f.py:x"), ["x"])

    def test_parse_trail_caps_depth(self):
        deep = ">".join(f"n{i}" for i in range(20))
        self.assertEqual(len(mod.parse_trail(deep)), mod.MAX_DEPTH)

    def test_parse_trail_hostile(self):
        self.assertEqual(mod.parse_trail(None), [])
        self.assertEqual(mod.parse_trail(42), [])
        self.assertEqual(mod.parse_trail(""), [])

    def test_trail_html_renders_breadcrumb(self):
        out = mod.trail_html("a>b", "m1")
        self.assertIn("id='rabbithole'", out)
        self.assertIn("depth 2", out)
        self.assertIn("?trail=a", out)
        self.assertIn("climb out", out)
        self.assertIn("no grading impact", out)

    def test_trail_html_empty_and_escapes(self):
        self.assertEqual(mod.trail_html("", "m"), "")
        self.assertEqual(mod.trail_html(None, "m"), "")
        out = mod.trail_html("<script>", "m")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script", out)  # ">" splits first (separator)

    def test_wander_html_extends_chain(self):
        lesson = {"callers": ["b"], "callees": ["zzz"]}
        out = mod.wander_html(lesson, "a", "m", known={"b"})
        self.assertIn("?trail=a>b", out)
        self.assertIn("#lesson-b", out)
        self.assertNotIn("zzz", out)

    def test_wander_html_drops_visited_and_unknown(self):
        lesson = {"callers": ["a"], "callees": []}
        self.assertEqual(mod.wander_html(lesson, "a", "m", known={"a"}), "")
        self.assertEqual(mod.wander_html(lesson, "", "m", known={"a"}), "")
        self.assertEqual(mod.wander_html(None, "a", "m"), "")


class RabbitholeEffectTest(unittest.TestCase):
    def test_module_page_with_trail_gains_banner(self):
        _tmp, db, _server, out = make_module("rabbit mod")
        body = handler_for(db).module_html(out["module_id"], trail="add")
        self.assertIn("id='rabbithole'", body)

    def test_module_page_without_trail_is_legacy(self):
        _tmp, db, _server, out = make_module("rabbit legacy mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("rabbithole", body)
        self.assertNotIn("Wander further", body)


class RabbitholeShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
