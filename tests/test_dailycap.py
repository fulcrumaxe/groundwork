"""Daily review cap with load-balanced overflow (I-205)."""
import copy
import unittest
from datetime import date

from groundwork import dailycap as dmod

from test_web import handler_for, make_module


def _card(cid, due="2026-09-20T00:00:00Z"):
    return {"id": cid, "due": due}


def _due(n):
    return [_card(f"c{i:02d}") for i in range(n)]


class ParseCapTest(unittest.TestCase):
    def test_valid_int_and_string(self):
        self.assertEqual(dmod.parse_cap(10), 10)
        self.assertEqual(dmod.parse_cap("20"), 20)
        self.assertEqual(dmod.parse_cap(" 5 "), 5)

    def test_absent_fails_closed_to_default(self):
        self.assertIsNone(dmod.parse_cap(None))
        self.assertIsNone(dmod.parse_cap(""))
        self.assertIsNone(dmod.parse_cap("   "))
        self.assertEqual(dmod.parse_cap(None, 7), 7)

    def test_garbage_fails_closed(self):
        for bad in ("junk", "10x", "NaN", 0, -3, "-2", True, False,
                    [], {}, object()):
            self.assertIsNone(dmod.parse_cap(bad), bad)

    def test_clamps_to_max(self):
        self.assertEqual(dmod.parse_cap(9999), dmod.MAX_CAP)
        self.assertEqual(dmod.parse_cap("1000"), dmod.MAX_CAP)

    def test_min_is_one(self):
        self.assertEqual(dmod.parse_cap(1), 1)
        self.assertIsNone(dmod.parse_cap(0))


class SplitTest(unittest.TestCase):
    def test_today_share_plus_dated_buckets(self):
        today, plan = dmod.split_due(_due(25), 10,
                                     start=date(2026, 9, 28))
        self.assertEqual([c["id"] for c in today],
                         [f"c{i:02d}" for i in range(10)])
        self.assertEqual(len(plan), 2)
        self.assertEqual(plan[0]["date"], "2026-09-28")
        self.assertEqual(plan[1]["date"], "2026-09-29")
        self.assertEqual([c["id"] for c in plan[0]["cards"]],
                         [f"c{i:02d}" for i in range(10, 20)])
        self.assertEqual([c["id"] for c in plan[1]["cards"]],
                         [f"c{i:02d}" for i in range(20, 25)])

    def test_order_preserved_no_resort(self):
        due = list(reversed(_due(12)))
        today, plan = dmod.split_due(due, 5)
        self.assertEqual([c["id"] for c in today],
                         [c["id"] for c in due[:5]])
        self.assertEqual([c["id"] for b in plan for c in b["cards"]],
                         [c["id"] for c in due[5:]])

    def test_deterministic(self):
        a = dmod.split_due(_due(23), "10", start="2026-09-28")
        b = dmod.split_due(_due(23), 10, start=date(2026, 9, 28))
        self.assertEqual(a, b)

    def test_never_mutates_input(self):
        due = _due(15)
        before = copy.deepcopy(due)
        today, _plan = dmod.split_due(due, 6)
        self.assertEqual(due, before)
        self.assertIsNot(today, due)

    def test_fits_today_empty_plan(self):
        today, plan = dmod.split_due(_due(4), 10)
        self.assertEqual(len(today), 4)
        self.assertEqual(plan, [])

    def test_empty_queue(self):
        self.assertEqual(dmod.split_due([], 10), ([], []))
        self.assertEqual(dmod.split_due(None, 10), ([], []))

    def test_skips_non_dicts(self):
        today, plan = dmod.split_due(
            [_card("a"), "junk", None, _card("b")], 1)
        self.assertEqual([c["id"] for c in today], ["a"])
        self.assertEqual(len(plan), 1)

    def test_per_day_spreads_load(self):
        _today, plan = dmod.split_due(_due(10), 8, per_day=1,
                                      start=date(2026, 9, 28))
        self.assertEqual(len(plan), 2)
        self.assertEqual([b["date"] for b in plan],
                         ["2026-09-28", "2026-09-29"])

    def test_bad_start_matches_default(self):
        _t, a = dmod.split_due(_due(12), 10, start="junk")
        _t, b = dmod.split_due(_due(12), 10)
        self.assertEqual(a, b)

    def test_never_raises(self):
        sentinel = object()
        today, plan = dmod.split_due(sentinel, 10)
        self.assertIs(today, sentinel)
        self.assertEqual(plan, [])


class CallerEffectTest(unittest.TestCase):
    def test_cap_changes_queue_count_and_surface(self):
        due = _due(25)
        today, plan = dmod.apply_cap(due, "10",
                                     start=date(2026, 9, 28))
        self.assertEqual(len(today), 10)  # capped queue, not 25
        self.assertEqual([c["id"] for c in today],
                         [f"c{i:02d}" for i in range(10)])
        box = dmod.cap_box(today, plan, "10")
        self.assertIn("showing 10 of 25", box)
        self.assertIn("spread over 2 coming days", box)
        self.assertIn("2026-09-28", box)

    def test_legacy_full_queue_pinned_without_cap(self):
        due = _due(25)
        today, plan = dmod.apply_cap(due, None)
        self.assertIs(today, due)  # untouched, not a copy
        self.assertEqual(plan, [])
        self.assertEqual(dmod.cap_box(today, plan, None), "")

    def test_garbage_cap_pins_legacy_queue(self):
        due = _due(25)
        today, plan = dmod.apply_cap(due, "junk")
        self.assertIs(today, due)
        self.assertEqual(plan, [])


class DueCallerTest(unittest.TestCase):
    # Real caller proof: Handler.due_html honors ?cap=.

    def test_due_html_caps_queue_and_shows_plan(self):
        tmp, db, server, out = make_module("dailycap caller")
        h = handler_for(db)
        full = h.due_html()
        capped = h.due_html(cap="1")
        self.assertEqual(full.count("<article"), 2)
        self.assertEqual(capped.count("<article"), 1)
        self.assertNotIn("id='dailycap'", full)
        self.assertIn("id='dailycap'", capped)
        self.assertIn("id='dailycap-plan'", capped)
        self.assertIn("showing 1 of 2", capped)

    def test_due_html_garbage_cap_is_legacy(self):
        tmp, db, server, out = make_module("dailycap legacy")
        h = handler_for(db)
        self.assertEqual(h.due_html(cap="junk"), h.due_html())
        self.assertNotIn("id='dailycap'", h.due_html(cap="junk"))


class BannerTest(unittest.TestCase):
    def test_empty_without_cap(self):
        today, plan = dmod.split_due(_due(25), None)
        self.assertEqual(dmod.cap_box(today, plan, None), "")

    def test_overflow_banner_counts_links(self):
        today, plan = dmod.split_due(_due(25), 10,
                                     start=date(2026, 9, 28))
        box = dmod.cap_box(today, plan, 10)
        self.assertIn("id='dailycap'", box)
        self.assertIn("id='dailycap-plan'", box)
        self.assertIn("Daily cap 10", box)
        self.assertIn("/due?cap=10", box)
        self.assertIn("full queue", box)

    def test_fits_today_note(self):
        today, plan = dmod.split_due(_due(4), 10)
        box = dmod.cap_box(today, plan, 10)
        self.assertIn("all 4 due fit today", box)
        self.assertNotIn("dailycap-plan", box)

    def test_mode_preserved_in_links(self):
        today, plan = dmod.split_due(_due(25), 10)
        box = dmod.cap_box(today, plan, 10, mode="one")
        self.assertIn("/due?mode=one&cap=10", box)
        self.assertIn("href='/due?mode=one'", box)

    def test_escapes_hostile_dates(self):
        box = dmod.cap_box([_card("a")],
                           [{"date": "<b>x", "cards": [_card("b")]}], 1)
        self.assertIn("&lt;b&gt;x", box)
        self.assertNotIn("<b>x", box)

    def test_status_section_anchor(self):
        body = dmod.section_html()
        self.assertIn("id='status-b29-dailycap'", body)
        self.assertIn("groundwork/dailycap.py", body)
        self.assertIn(dmod.STATUS_ANCHOR, body)

    def test_tour_entry_shape(self):
        e = dmod.tour_entry()
        self.assertEqual(e["id"], "daily-cap")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], dmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
