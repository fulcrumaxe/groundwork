"""Refactoring kata library (F-87)."""
import unittest

from groundwork import katabank as kbmod
from groundwork import smell as smellmod

from test_web import make_module


def _card(cid, smell=None):
    payload = {"smell": smell} if smell else {}
    return {"id": cid, "concept_id": "m:c", "exercise_type": 15,
            "payload": payload}


class TracksTest(unittest.TestCase):
    def test_track_ids_match_smell_catalog(self):
        self.assertEqual(set(kbmod.TRACK_IDS), set(smellmod.BY_ID))
        for track in kbmod.TRACKS:
            self.assertGreaterEqual(len(track["katas"]), 1)
            for kata in track["katas"]:
                self.assertTrue(kata["code"].strip())
                self.assertTrue(kata["fix"].strip())


class IsDueTest(unittest.TestCase):
    def test_never_tried_is_due(self):
        self.assertTrue(kbmod.is_due({}))
        self.assertTrue(kbmod.is_due(None))
        self.assertTrue(kbmod.is_due({"passes": 3, "last": ""}))

    def test_week_old_is_due_fresh_is_not(self):
        self.assertTrue(kbmod.is_due({"passes": 1, "last": "2020-01-01"},
                                     now="2020-02-01"))
        self.assertFalse(kbmod.is_due({"passes": 1, "last": "2020-01-30"},
                                      now="2020-02-01"))


class PickKataTest(unittest.TestCase):
    def test_weakest_due_non_last_wins(self):
        history = {"long-function": {"passes": 5, "fails": 0,
                                     "last": "2020-01-01"},
                   "broad-except": {"passes": 0, "fails": 3,
                                    "last": "2020-01-01"}}
        self.assertEqual(
            kbmod.pick_kata(history, None, "long-function",
                            now="2020-02-01"), "broad-except")

    def test_single_track_deals_and_empty_history(self):
        self.assertEqual(kbmod.pick_kata({}, ["magic-numbers"]),
                         "magic-numbers")
        self.assertIn(kbmod.pick_kata({}), kbmod.TRACK_IDS)

    def test_garbage_never_raises(self):
        self.assertIn(kbmod.pick_kata(None, None, None), kbmod.TRACK_IDS)
        self.assertIsNone(kbmod.pick_kata({"broad-except": "nope"},
                                          ["broad-except"], "broad-except"))
        self.assertIsNone(kbmod.pick_kata({}, [], ""))


class HistoryTest(unittest.TestCase):
    def test_rows_build_stats(self):
        rows = [{"grade": 5, "reviewed_at": "2020-01-02",
                 "payload": {"smell": "broad-except"}},
                {"grade": 1, "reviewed_at": "2020-01-03",
                 "payload": '{"smell": "broad-except"}'},
                {"grade": 5, "reviewed_at": "2020-01-01",
                 "payload": {"smell": "nope"}},
                {"grade": "x", "reviewed_at": "2020-01-01",
                 "payload": {"smell": "broad-except"}}]
        got = kbmod.kata_history_from_rows(rows)
        self.assertEqual(got["broad-except"]["passes"], 1)
        self.assertEqual(got["broad-except"]["fails"], 1)
        self.assertEqual(got["broad-except"]["last"], "2020-01-03")
        self.assertNotIn("nope", got)


class OrderDueTest(unittest.TestCase):
    def test_empty_history_keeps_interleave_order(self):
        from groundwork import sched as schedmod
        cards = [_card("a", "long-function"), _card("b", "broad-except"),
                 _card("c")]
        self.assertEqual(kbmod.order_due(cards, None),
                         schedmod.interleave(cards))
        self.assertEqual(kbmod.order_due(cards, {}),
                         schedmod.interleave(cards))

    def test_weakest_track_first(self):
        cards = [_card("a", "long-function"), _card("b", "broad-except"),
                 _card("c")]
        history = {"long-function": {"passes": 1, "fails": 0,
                                     "last": "2020-01-31"},
                   "broad-except": {"passes": 0, "fails": 1,
                                    "last": "2020-01-22"}}
        out = kbmod.order_due(cards, history, now="2020-02-01")
        self.assertEqual([c["id"] for c in out], ["b", "a", "c"])

    def test_garbage_keeps_order(self):
        cards = [_card("a", "broad-except")]
        self.assertEqual(kbmod.order_due(None, None), [])
        self.assertEqual(kbmod.order_due("nope", {}), [])
        self.assertEqual([c["id"] for c in kbmod.order_due(cards, 42)], ["a"])


class CallerEffectTest(unittest.TestCase):
    def test_due_reviews_keep_order_without_kata_history(self):
        from groundwork import interleave as interleavemod
        from groundwork import mcp as mcplib
        tmp, db, server, out = make_module("katabank mod")
        mcplib_server = mcplib.MCPServer(db)
        got = mcplib_server.tool_list_due_reviews({"limit": 20})["due"]
        self.assertTrue(got)
        # No smell reviews exist: kata layer returns interleave order.
        plain = interleavemod.order_due([dict(c) for c in got], {})
        self.assertEqual([c["id"] for c in got],
                         [c["id"] for c in plain])

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{kbmod.STATUS_ANCHOR}'",
                      kbmod.section_html())
        e = kbmod.tour_entry()
        self.assertEqual(e["id"], "refactoring-katas")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], kbmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
