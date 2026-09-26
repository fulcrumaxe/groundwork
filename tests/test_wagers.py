"""Friendly wagers (F-128): coffee bets on delayed-test outcomes."""
import unittest

from test_web import make_module

from groundwork import history as histmod
from groundwork import wagers as wmod


def probe_wager(**kw):
    base = {"kind": "probe", "card_id": 7, "window": 7, "target": None,
            "bettor": "you", "rival": "sam", "stake": "coffee",
            "status": "open", "placed_at": ""}
    base.update(kw)
    return base


class PlaceProbeTest(unittest.TestCase):
    def test_defaults(self):
        w = wmod.place_probe_wager(7)
        self.assertEqual(w["kind"], "probe")
        self.assertEqual(w["window"], 7)
        self.assertEqual(w["stake"], "coffee")
        self.assertEqual(w["status"], "open")

    def test_bad_window_falls_back(self):
        self.assertEqual(wmod.place_probe_wager(1, 99)["window"], 7)
        self.assertEqual(wmod.place_probe_wager(1, "x")["window"], 7)
        self.assertEqual(wmod.place_probe_wager(1, 30)["window"], 30)

    def test_garbage_card_id_loggable(self):
        self.assertIn("status", wmod.place_probe_wager(None))

    def test_place_accuracy_clamps(self):
        self.assertEqual(wmod.place_accuracy_wager(2.0)["target"], 1.0)
        self.assertEqual(wmod.place_accuracy_wager(-1.0)["target"], 0.0)
        self.assertEqual(wmod.place_accuracy_wager("x")["target"], 0.8)


class QueryTest(unittest.TestCase):
    def test_colon_specs(self):
        rows = wmod.wagers_from_query({"wager": ["probe:c1:30", "acc:0.9"]})
        self.assertEqual(rows[0]["window"], 30)
        self.assertEqual(rows[0]["card_id"], "c1")
        self.assertEqual(rows[1]["target"], 0.9)

    def test_card_ids_with_colons(self):
        rows = wmod.wagers_from_query({"wager": ["probe:mod1:ex001:7"]})
        self.assertEqual(rows[0]["card_id"], "mod1:ex001")
        self.assertEqual(rows[0]["window"], 7)

    def test_discrete_form_fields(self):
        rows = wmod.wagers_from_query({"wager_kind": ["probe"],
                                       "wager_card": ["c9"],
                                       "wager_window": ["30"]})
        self.assertEqual(rows[0]["card_id"], "c9")
        self.assertEqual(rows[0]["window"], 30)

    def test_nothing_placed_gives_empty(self):
        self.assertEqual(wmod.wagers_from_query({}), [])
        self.assertEqual(wmod.wagers_from_query(None), [])
        self.assertEqual(wmod.wagers_from_query({"wager": ["junk"]}), [])


class SettleTest(unittest.TestCase):
    def test_probe_pass_wins(self):
        self.assertEqual(
            wmod.settle(probe_wager(), {"grade": 4})["status"], "won")
        self.assertEqual(
            wmod.settle(probe_wager(), {"grade": 5})["status"], "won")

    def test_probe_fail_loses(self):
        self.assertEqual(
            wmod.settle(probe_wager(), {"grade": 3})["status"], "lost")

    def test_missing_grade_stays_open(self):
        self.assertEqual(wmod.settle(probe_wager(), {})["status"], "open")
        self.assertEqual(
            wmod.settle(probe_wager(), {"grade": "x"})["status"], "open")
        self.assertEqual(wmod.settle(probe_wager(), None)["status"], "open")

    def test_accuracy_settles_on_snapshot(self):
        w = wmod.place_accuracy_wager(0.8)
        self.assertEqual(
            wmod.settle(w, {"delayed_acc": 0.9})["status"], "won")
        self.assertEqual(
            wmod.settle(w, {"delayed_acc": 0.5})["status"], "lost")

    def test_no_mature_data_stays_open(self):
        w = wmod.place_accuracy_wager(0.8)
        self.assertEqual(
            wmod.settle(w, {"delayed_acc": None})["status"], "open")

    def test_settled_wager_untouched(self):
        w = probe_wager(status="won")
        self.assertEqual(wmod.settle(w, {"grade": 1})["status"], "won")

    def test_never_raises(self):
        wmod.settle(None, None)
        wmod.settle("x", "y")
        wmod.settle(probe_wager(), {"delayed_acc": float("nan")})

    def test_settle_all_uses_live_grades(self):
        rows = wmod.settle_all([probe_wager(card_id="c1")], {"c1": 5}, None)
        self.assertEqual(rows[0]["status"], "won")
        rows = wmod.settle_all([probe_wager(card_id="c1")], {"c1": 2}, None)
        self.assertEqual(rows[0]["status"], "lost")
        rows = wmod.settle_all([probe_wager(card_id="c9")], {"c1": 5}, None)
        self.assertEqual(rows[0]["status"], "open")


class LedgerTest(unittest.TestCase):
    def test_counts(self):
        rows = [probe_wager(status="won"), probe_wager(status="lost"),
                probe_wager()]
        s = wmod.ledger_summary(rows)
        self.assertEqual((s["n"], s["won"], s["lost"], s["open"]), (3, 1, 1, 1))
        self.assertEqual((s["coffees_won"], s["coffees_owed"]), (1, 1))

    def test_garbage_ledger_empty(self):
        self.assertEqual(wmod.ledger_summary(None)["n"], 0)
        self.assertEqual(wmod.ledger_summary("x")["n"], 0)


class RenderTest(unittest.TestCase):
    def test_empty_renders_anchor(self):
        out = wmod.section_html([])
        self.assertIn("id='status-wagers'", out)
        self.assertIn("No wagers yet", out)
        self.assertIn("wager-place", out)

    def test_rows_render(self):
        out = wmod.section_html([probe_wager(status="won")])
        self.assertIn("owes", out)
        self.assertIn("coffee", out)

    def test_tour_entry(self):
        e = wmod.tour_entry()
        self.assertEqual(e["id"], "friendly-wagers")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["path"], "/reviews")
        self.assertEqual(e["anchor"], "status-wagers")

    def test_status_page_anchor(self):
        self.assertIn(f"id='{wmod.STATUS_PAGE_ANCHOR}'",
                      wmod.status_section_html())


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_empty_ledger(self):
        _tmp, db, _s, _out = make_module("wagers empty")
        body = histmod.history_html(db)
        self.assertIn("id='status-wagers'", body)
        self.assertIn("No wagers yet", body)
        self.assertIn("wager-place", body)

    def test_probe_bet_settles_against_live_grade(self):
        _tmp, db, server, _out = make_module("wagers live")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = histmod.history_html(db, {"wager": [f"probe:{card['id']}:7"]})
        self.assertIn("id='status-wagers'", body)
        self.assertIn("won", body)
        self.assertIn("owes", body)

    def test_accuracy_bet_stays_open_without_mature_data(self):
        _tmp, db, _s, _out = make_module("wagers acc")
        body = histmod.history_html(db, {"wager": ["acc:0.9"]})
        self.assertIn("open, a coffee riding on it", body)


if __name__ == "__main__":
    unittest.main()
