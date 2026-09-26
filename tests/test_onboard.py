"""Onboarding countdown: day N of 30 + core-flow checklist (F-135)."""
import unittest

from groundwork import emoji as emojimod
from groundwork import onboard as mod
from test_web import handler_for, make_module


class OnboardUnitTest(unittest.TestCase):
    def test_day_boundaries(self):
        self.assertEqual(mod.day_of("2026-09-20", "2026-09-20"), 1)
        self.assertTrue(mod.is_active("2026-09-20", "2026-09-20"))
        self.assertTrue(mod.is_active("2026-08-22", "2026-09-20"))
        self.assertFalse(mod.is_active("2026-08-21", "2026-09-20"))
        self.assertFalse(mod.is_active("", "2026-09-20"))
        self.assertFalse(mod.is_active("junk", "junk"))
        self.assertEqual(mod.day_of("2026-09-25", "2026-09-20"), 1)

    def test_first_seen_earliest_wins(self):
        rows = {"c1": [{"reviewed_at": "2026-09-20T10:00:00Z"},
                       {"reviewed_at": "2026-09-10T10:00:00Z"}],
                "c2": [{"when": "2026-09-15T10:00:00Z"}, None, {}]}
        self.assertEqual(mod.first_seen_from(rows), "2026-09-10T10:00:00Z")
        self.assertEqual(
            mod.first_seen_from([{"reviewed_at": "2026-09-01T00:00:00Z"}]),
            "2026-09-01T00:00:00Z")
        self.assertEqual(mod.first_seen_from(None), "")
        self.assertEqual(mod.first_seen_from([None, {}]), "")

    def test_core_flows_entry_first_then_indegree(self):
        lessons = [{"name": "serve", "needs": ["parse", "grade"]},
                   {"name": "parse"}, {"name": "grade", "needs": ["parse"]}]
        flows = mod.core_flows(lessons)
        self.assertEqual([f["name"] for f in flows],
                         ["parse", "grade", "serve"])
        self.assertEqual(mod.core_flows(lessons, limit=2), flows[:2])
        self.assertEqual(mod.core_flows(None), [])
        self.assertEqual(mod.core_flows(lessons, limit=0), [])

    def test_checklist_marks_owned(self):
        flows = [{"name": "parse", "key": "m:parse"}]
        done = mod.checklist(flows, {"m:parse": (2, True)})
        self.assertTrue(done[0]["done"])
        todo = mod.checklist(flows, {"m:other": (2, True)})
        self.assertFalse(todo[0]["done"])
        via_set = mod.checklist(flows, {"parse"})
        self.assertTrue(via_set[0]["done"])

    def test_banner_and_empty_states(self):
        out = mod.countdown_box_html(
            first_seen="2026-09-18", now="2026-09-20",
            lessons=[{"name": "parse<script>"}])
        self.assertIn("id='onboard'", out)
        self.assertIn("Day 3 of 30", out)
        self.assertIn("[ ]", out)
        self.assertNotIn("<script>", out)
        self.assertEqual(mod.countdown_box_html(rows=[]), "")
        self.assertEqual(
            mod.countdown_box_html(first_seen="2026-01-01",
                                   now="2026-09-20"), "")


class OnboardEffectTest(unittest.TestCase):
    def test_module_page_without_reviews_is_legacy(self):
        _tmp, db, _server, out = make_module("onboard legacy mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("id='onboard'", body)

    def test_module_page_with_review_gains_countdown(self):
        _tmp, db, server, out = make_module("onboard live mod")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("id='onboard'", body)
        self.assertIn("Day 1 of 30", body)


class OnboardShapeTest(unittest.TestCase):
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
