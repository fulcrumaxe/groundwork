"""Guardian view: ?guardian=1 aggregate-only History for parents (F-170)."""
import unittest

from groundwork import emoji as emojimod
from groundwork import guardian as mod
from test_web import handler_for, make_module


class GuardianUnitTest(unittest.TestCase):
    def test_flag_parsing(self):
        self.assertTrue(mod.is_guardian({"guardian": ["1"]}))
        self.assertTrue(mod.is_guardian({"guardian": ["0", "1"]}))
        self.assertTrue(mod.is_guardian("1"))
        self.assertFalse(mod.is_guardian({"guardian": ["0"]}))
        self.assertFalse(mod.is_guardian({"guardian": ["yes"]}))
        self.assertFalse(mod.is_guardian({"guardian": []}))
        self.assertFalse(mod.is_guardian({"kids": ["1"]}))
        self.assertFalse(mod.is_guardian({}))
        self.assertFalse(mod.is_guardian(None))

    def test_flag_never_raises(self):
        for bad in (None, {}, {"guardian": [None]}, 0, ["1"], object()):
            self.assertFalse(mod.is_guardian(bad))

    def test_effort_band(self):
        self.assertEqual(mod.effort_band(0), "resting")
        self.assertEqual(mod.effort_band(1), "light")
        self.assertEqual(mod.effort_band(4), "light")
        self.assertEqual(mod.effort_band(5), "steady")
        self.assertEqual(mod.effort_band(14), "steady")
        self.assertEqual(mod.effort_band(15), "strong")
        self.assertEqual(mod.effort_band(99), "strong")
        for bad in (None, -3, "x", object()):
            self.assertEqual(mod.effort_band(bad), "resting")

    def test_view_aggregates_only(self):
        _tmp, db, _server, _out = make_module("guardian agg mod")
        view = mod.view_html(db)
        self.assertIn(f"id='{mod.VIEW_ANCHOR}'", view)
        self.assertIn("1 projects", view)
        self.assertIn("ideas owned", view)
        self.assertIn("Last 7 days", view)
        self.assertIn("week", view)
        self.assertIn("/reviews", view)
        self.assertTrue(view.isascii())
        self.assertEqual(emojimod.scan_text(view), [])

    def test_view_carries_no_surveillance_detail(self):
        _tmp, db, server, _out = make_module("guardian leak mod")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        view = mod.view_html(db)
        self.assertIn("1 tries", view)
        for marker in ("grade", "confidence", "reviewed_at", "card_id",
                       "Calibration", "id='attempts'", "id='calibration'"):
            self.assertNotIn(marker, view)
        self.assertNotIn(card["front"], view)

    def test_view_never_raises(self):
        for bad in ("", None):
            self.assertIn("0 projects", mod.view_html(bad))


class GuardianEffectTest(unittest.TestCase):
    def test_legacy_bytes_without_flag(self):
        _tmp, db, _server, _out = make_module("guardian legacy mod")
        body = handler_for(db).history_html(None)
        self.assertNotIn("guardian-view", body)
        self.assertEqual(handler_for(db).history_html({}), body)
        self.assertEqual(handler_for(db).history_html({"guardian": ["0"]}),
                         body)

    def test_guardian_flag_swaps_empty_history(self):
        _tmp, db, _server, _out = make_module("guardian live mod")
        body = handler_for(db).history_html({"guardian": ["1"]})
        self.assertIn(f"id='{mod.VIEW_ANCHOR}'", body)
        self.assertIn("Guardian view", body)
        self.assertIn("0 tries", body)
        self.assertNotIn("id='attempts'", body)
        self.assertNotIn("No attempts yet.", body)
        self.assertNotIn("Calibration", body)

    def test_reviewed_history_hides_detail(self):
        _tmp, db, server, _out = make_module("guardian full mod")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        legacy = handler_for(db).history_html(None)
        self.assertIn("grade", legacy)
        self.assertIn("id='attempts'", legacy)
        body = handler_for(db).history_html({"guardian": ["1"]})
        self.assertIn(f"id='{mod.VIEW_ANCHOR}'", body)
        self.assertIn("1 tries", body)
        for marker in ("grade", "confidence", "Calibration",
                       "id='attempts'", "id='calibration'"):
            self.assertNotIn(marker, body)
        self.assertNotIn(card["front"], body)


class GuardianShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["id"], "guardian-view")
        self.assertEqual(e["anchor"], mod.STATUS_ANCHOR)

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())
        self.assertIn("?guardian=1", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])
        self.assertTrue(src.isascii())


if __name__ == "__main__":
    unittest.main()
