"""Batch 15 integration: points banked, odds shown, cards dealt, probes listed.

F-65 banks score() per submit (verdict + History show it); F-66 puts
explicit odds on the confidence widget and settles the bet on the
verdict; F-67 deals overconf cards from live calibration rows;
F-51 resurfaces probe-due owned cards in Due and stamps last_probe.
Per the Integration rule each test proves a BEHAVIORAL effect, with
legacy fallbacks (no points column data, no mastery, few attempts,
fresh cards) pinned quiet.
"""
import sqlite3
import unittest

from groundwork import calibdrill as drillmod
from groundwork import cards as cardsmod
from groundwork import confslider as confmod
from groundwork import history as histmod
from groundwork import overconf as ocmod
from groundwork import ownership as ownmod
from groundwork import results as resmod

from test_web import make_module


def _seed_reviews(db, card_id, grades, conf=4, days_ago=None):
    con = sqlite3.connect(db)
    try:
        con.executemany(
            "INSERT INTO reviews(card_id, grade, confidence) VALUES(?,?,?)",
            [(card_id, g, conf) for g in grades])
        if days_ago is not None:
            con.execute(
                "UPDATE reviews SET reviewed_at ="
                " strftime('%Y-%m-%dT%H:%M:%SZ','now', ?)"
                " WHERE card_id = ?", (f"-{int(days_ago)} days", card_id))
        con.commit()
    finally:
        con.close()


class PointsBankTest(unittest.TestCase):
    def test_submit_banks_score(self):
        tmp, db, server, out = make_module("points live")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        out = server.submit_review(card["id"], "5", 4)
        self.assertEqual(out["points"], 4)
        con = sqlite3.connect(db)
        try:
            pts = con.execute(
                "SELECT points FROM reviews WHERE card_id=?",
                (card["id"],)).fetchone()[0]
        finally:
            con.close()
        self.assertEqual(pts, 4)

    def test_brave_wrong_costs(self):
        tmp, db, server, out = make_module("points cost")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        out = server.submit_review(card["id"], "1", 5)
        self.assertEqual(out["points"], -5)

    def test_verdict_shows_banked_line(self):
        html = resmod.render_result(True, "good", "why", "2026-01-01",
                                    "/", "m", 0, points=4)
        self.assertIn("banked +4", html)
        html = resmod.render_result(False, "bad", "why", "2026-01-01",
                                    "/", "m", 0, points=-5)
        self.assertIn("banked -5", html)
        plain = resmod.render_result(True, "good", "why", "2026-01-01",
                                     "/", "m", 0)
        self.assertNotIn("banked", plain)

    def test_history_totals_bank(self):
        tmp, db, server, out = make_module("bank total")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        html = histmod.history_html(db)
        self.assertIn("bank +4 pts", html)


class DrillOddsTest(unittest.TestCase):
    def test_odds_line_shape(self):
        line = confmod.odds_html()
        self.assertIn("class='odds'", line)
        self.assertIn("1→+8/-2", line)
        self.assertIn("5→+0/-10", line)
        self.assertIsInstance(confmod.odds_html(), str)

    def test_widget_carries_odds(self):
        self.assertIn("Odds", cardsmod._confidence())
        self.assertIn("confslider-seg", cardsmod._confidence())

    def test_verdict_settles_bet(self):
        tmp, db, server, out = make_module("drill live")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        out = server.submit_review(card["id"], "5", 4)
        # Stated 80%: fair odds +2/-8, correct settles +2.
        self.assertIn("stated 80%", out["drill"])
        self.assertIn("settled +2", out["drill"])
        html = resmod.render_result(True, "g", "w", "d", "/", "m", 0,
                                    points=out["points"], drill=out["drill"])
        self.assertIn("stated 80%", html)
        plain = resmod.render_result(True, "g", "w", "d", "/", "m", 0)
        self.assertNotIn("Drill:", plain)


class OverconfLiveTest(unittest.TestCase):
    def test_silent_under_floor_or_underconfident(self):
        few = [("recall", 2, 5)] * 9
        self.assertEqual(ocmod.coach_card(few), "")
        self.assertEqual(ocmod.coach_card(None), "")
        modest = [("recall", 5, 1)] * 12
        self.assertEqual(ocmod.coach_card(modest), "")

    def test_fires_on_live_gap_naming_weakest(self):
        rows = [("recall", 2, 5)] * 8 + [("apply", 2, 5)] * 4
        card = ocmod.coach_card(rows)
        self.assertIn("overconf-card", card)
        self.assertIn("recall", card)
        # Garbage rows never break the card.
        self.assertIn("overconf-card",
                      ocmod.coach_card(rows + [None, "junk", ("x",)]))

    def test_history_deals_live_card(self):
        tmp, db, server, out = make_module("coach live")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        _seed_reviews(db, card["id"], [2] * 12, conf=5)
        html = histmod.history_html(db)
        self.assertIn("overconf-card", html)


class ProbeQueueTest(unittest.TestCase):
    def test_fresh_queue_has_no_probes(self):
        tmp, db, server, out = make_module("probe quiet")
        due = server.tool_list_due_reviews({"limit": 20})["due"]
        self.assertTrue(due)
        self.assertFalse(any(c.get("probe") for c in due))

    def test_probe_resurfaces_and_records(self):
        # Hand-built cycle (generated modules never produce
        # ownership-qualifying types): owned (2x grade 5 on a
        # modify-type card) + stable, last review 8 days back, due
        # pushed out so only the probe window can list it.
        import tempfile
        from pathlib import Path
        from groundwork import db as dbmod
        from groundwork import mcp as mcplib
        from groundwork import sched as schedmod
        tmp = Path(tempfile.mkdtemp(prefix="gw-probe-"))
        db = str(tmp / "probe.db")
        dbmod.init_db(db)
        past = (schedmod.utcnow() -
                __import__("datetime").timedelta(days=8)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        future = (schedmod.utcnow() +
                  __import__("datetime").timedelta(days=30)).strftime(
            "%Y-%m-%dT%H:%M:%SZ")
        con = sqlite3.connect(db)
        try:
            con.execute(
                "INSERT INTO modules(id, task_summary, repo, commit_range)"
                " VALUES(?,?,?,?)", ("m1", "probe mod", ".", "x"))
            con.execute(
                "INSERT INTO concepts(id, module_id, name)"
                " VALUES(?,?,?)", ("m1:c1", "m1", "loops"))
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front,"
                " back, stability, difficulty, due)"
                " VALUES(?,?,?,?,?,?,?,?)",
                ("m1:c1:ex1", "m1:c1", "12", "trace it", "traced",
                 30.0, 0.5, future))
            con.executemany(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at) VALUES(?,?,?,?)",
                [("m1:c1:ex1", 5, 4, past)] * 2)
            con.commit()
        finally:
            con.close()
        server = mcplib.MCPServer(db)
        due2 = server.tool_list_due_reviews({"limit": 20})["due"]
        probe = next(c for c in due2 if c["id"] == "m1:c1:ex1")
        self.assertEqual(probe["probe"], 7)
        # Answering the probe stamps last_probe (graders fail closed,
        # so any submission records without crashing)...
        r = server.submit_review("m1:c1:ex1", "xxx", 3)
        self.assertNotIn("error", r)
        con = sqlite3.connect(db)
        try:
            stamped = con.execute(
                "SELECT last_probe FROM cards WHERE id=?",
                ("m1:c1:ex1",)).fetchone()[0]
        finally:
            con.close()
        self.assertTrue(stamped)
        # ...and the cycle is covered: re-listed as plain due if due,
        # never probe-flagged twice.
        con = sqlite3.connect(db)
        try:
            con.execute(
                "UPDATE cards SET due ="
                " strftime('%Y-%m-%dT%H:%M:%SZ','now','-1 days')"
                " WHERE id = 'm1:c1:ex1'")
            con.commit()
        finally:
            con.close()
        due3 = server.tool_list_due_reviews({"limit": 20})["due"]
        again = next(c for c in due3 if c["id"] == "m1:c1:ex1")
        self.assertFalse(again.get("probe"))


if __name__ == "__main__":
    unittest.main()
