"""Post-answer what-to-review-next list (I-190)."""
import unittest

from groundwork import nextup as numod
from groundwork import results as resmod
from groundwork import scrollpos as scrollposmod

from test_web import make_module


class PickTest(unittest.TestCase):
    def test_excludes_answered_and_orders_by_due(self):
        tmp, db, server, out = make_module("nextup mod")
        due = server.tool_list_due_reviews({"limit": 20})["due"]
        self.assertGreaterEqual(len(due), 2)
        picks = numod.pick_next(db, due[0]["id"])
        self.assertTrue(picks)
        self.assertLessEqual(len(picks), numod.DEFAULT_LIMIT)
        for p in picks:
            self.assertNotEqual(p["card_id"], due[0]["id"])
            self.assertIn("due", p["reason"])
            self.assertIn("mastery", p["reason"])
        dues = [p["due"] for p in picks]
        self.assertEqual(dues, sorted(dues))

    def test_limits_and_hostile_input(self):
        tmp, db, server, out = make_module("nextup limits")
        self.assertEqual(numod.pick_next(db, "", limit=0), [])
        self.assertLessEqual(len(numod.pick_next(db, "", limit=99)),
                             numod.MAX_LIMIT)
        self.assertEqual(numod.pick_next(None), [])
        self.assertEqual(numod.pick_next(""), [])
        self.assertEqual(numod.pick_next(db, "", limit="nope").__class__, list)


class BoxTest(unittest.TestCase):
    def test_empty_renders_nothing(self):
        self.assertEqual(numod.box_html([]), "")
        self.assertEqual(numod.box_html(None), "")
        self.assertEqual(numod.box_html("nope"), "")

    def test_picks_render_queue_links_with_whysee(self):
        out = numod.box_html([{"card_id": "c1", "concept": "add <b>",
                               "reason": "due 2026-09-20; mastery 0.20"}])
        self.assertIn("id='nextup'", out)
        self.assertIn("/due#card-c1", out)
        self.assertIn("add &lt;b&gt;", out)
        self.assertIn("Why am I seeing this?", out)
        self.assertIn("due 2026-09-20", out)

    def test_nothing_due_stays_byte_identical(self):
        tmp, db, server, out = make_module("nextup legacy")
        self.assertEqual(numod.box_for(db, "", now="2000-01-01"), "")
        self.assertNotIn("nextup", resmod.render_result(
            True, "ok", "why", "tomorrow", "/due", "m1"))


class CallerEffectTest(unittest.TestCase):
    def test_submit_review_carries_nextup_box(self):
        tmp, db, server, out = make_module("nextup caller")
        due = server.tool_list_due_reviews({"limit": 20})["due"]
        first, rest = due[0]["id"], [c["id"] for c in due[1:]]
        out = server.submit_review(first, "5", 4)
        self.assertIn("nextup", out)
        box = out["nextup"]
        self.assertIn("id='nextup'", box)
        self.assertNotIn(scrollposmod.card_anchor(first), box)
        self.assertTrue(any(scrollposmod.card_anchor(c) in box for c in rest),
                        "box should link a still-due card")

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{numod.STATUS_ANCHOR}'",
                      numod.section_html())
        e = numod.tour_entry()
        self.assertEqual(e["id"], "what-next")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], numod.STATUS_ANCHOR)
        self.assertEqual(e["path"], "/status")


if __name__ == "__main__":
    unittest.main()
