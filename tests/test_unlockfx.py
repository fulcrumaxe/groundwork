"""Unlock animation for newly available lessons (I-148)."""
import unittest

from groundwork import unlockfx as mod

from test_web import handler_for, make_module


class FreshTest(unittest.TestCase):
    def test_fresh_when_prereqs_owned_self_not(self):
        self.assertTrue(
            mod.is_fresh("c", {"c": ["a", "b"]}, {"a", "b"}))

    def test_not_fresh_when_self_owned(self):
        self.assertFalse(
            mod.is_fresh("c", {"c": ["a"]}, {"a", "c"}))

    def test_not_fresh_when_prereq_missing(self):
        self.assertFalse(mod.is_fresh("c", {"c": ["a"]}, set()))
        self.assertFalse(mod.is_fresh("c", {}, set()))

    def test_hostile_never_raises(self):
        self.assertFalse(mod.is_fresh(None, None, None))
        self.assertFalse(mod.is_fresh("c", "nope", "nope"))
        self.assertEqual(mod.fresh_names(None, None), [])
        self.assertEqual(
            mod.fresh_names({"c": ["a"]}, {"a"}), ["c"])

    def test_badge_empty_when_not_fresh(self):
        self.assertEqual(mod.badge_html("c", False), "")
        body = mod.badge_html("c", True)
        self.assertIn("unlock-fx", body)
        self.assertIn("mo-reveal", body)

    def test_css_has_no_style_tags(self):
        css = mod.badge_css()
        self.assertNotIn("<style", css)
        self.assertIn("unlock-fx", css)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_badge_for_marks_newly_unlocked(self):
        lesson_map = {"a": {"callees": []}, "c": {"callees": ["a"]}}
        mastery = {"a": 0.9, "c": 0.1}
        self.assertIn("unlock-fx", mod.badge_for("c", lesson_map, mastery))
        self.assertEqual(mod.badge_for("a", lesson_map, mastery), "")
        self.assertEqual(
            mod.badge_for("c", lesson_map, {"a": 0.9, "c": 0.95}), "")

    def test_module_page_falls_back_without_edges(self):
        # Fixture lessons carry no callees: no unlocks, legacy bytes.
        _tmp, db, _s, out = make_module("unlockfx caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("unlock-fx mo-reveal", body)

    def test_wire_renders_badge_inside_section(self):
        # The one-line wire passes live map + mastery: a prereq-owned
        # lesson section carries the badge, owned sections do not.
        lesson_map = {"total": {"callees": []}, "add": {"callees": ["total"]}}
        mastery = {"total": 0.9, "add": 0.1}
        self.assertIn("unlock-fx",
                      mod.badge_for("add", lesson_map, mastery))
        self.assertEqual(mod.badge_for("total", lesson_map, mastery), "")


if __name__ == "__main__":
    unittest.main()
