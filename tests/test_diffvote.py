"""Per-lesson difficulty votes (I-145)."""
import unittest

from groundwork import db as dbmod
from groundwork import diffvote as mod

from test_web import handler_for, make_module


class NormalizeTest(unittest.TestCase):
    def test_synonyms(self):
        self.assertEqual(mod.normalize_vote("EASY"), "easy")
        self.assertEqual(mod.normalize_vote("too easy"), "easy")
        self.assertEqual(mod.normalize_vote("Just Right"), "just")
        self.assertEqual(mod.normalize_vote("TOO HARD"), "hard")

    def test_garbage_fails_closed(self):
        self.assertEqual(mod.normalize_vote(""), "")
        self.assertEqual(mod.normalize_vote(None), "")
        self.assertEqual(mod.normalize_vote(5), "")
        self.assertEqual(mod.normalize_vote("medium"), "")


class VerdictTest(unittest.TestCase):
    def test_plurality_wins(self):
        self.assertEqual(
            mod.verdict({"easy": 2, "just": 1, "hard": 0}), "Too easy")
        self.assertEqual(
            mod.verdict({"easy": 0, "just": 1, "hard": 3}), "Too hard")

    def test_tie_is_mixed(self):
        self.assertEqual(
            mod.verdict({"easy": 1, "just": 1, "hard": 1}), "Mixed")

    def test_empty_has_no_votes(self):
        self.assertEqual(mod.verdict({}), "No difficulty votes yet")
        self.assertEqual(mod.badge_html({}), "")


class RenderTest(unittest.TestCase):
    def test_badge_names_winner_and_counts(self):
        body = mod.badge_html({"easy": 0, "just": 1, "hard": 2})
        self.assertIn("Too hard", body)
        self.assertIn("2", body)

    def test_form_posts_three_values(self):
        form = mod.vote_form_html("m:add", "/modules/m")
        self.assertIn("/concepts/m:add/diffvote", form)
        self.assertIn("value='easy'", form)
        self.assertIn("value='just'", form)
        self.assertIn("value='hard'", form)

    def test_hostile_cid_renders_nothing(self):
        self.assertEqual(mod.vote_form_html("", "/m"), "")
        self.assertEqual(mod.vote_form_html(None, "/m"), "")

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_module_page_shows_form_without_badge(self):
        _tmp, db, _s, out = make_module("diffvote caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("value='easy'", body)
        self.assertNotIn("diffvote-badge", body)

    def test_recorded_vote_badges(self):
        _tmp, db, _s, out = make_module("diffvote recorded")
        h = handler_for(db)
        self.assertEqual(mod.tallies(db, []), {})
        con = dbmod.connect(db)
        try:
            con_cid = con.execute(
                "SELECT id AS cid FROM concepts").fetchall()[0]["cid"]
        finally:
            con.close()
        res = mod.record(db, con_cid, "hard")
        self.assertNotIn("error", res)
        body = h.module_html(out["module_id"])
        self.assertIn("diffvote-badge", body)
        self.assertIn("Too hard", body)

    def test_record_rejects_garbage(self):
        _tmp, db, _s, _out = make_module("diffvote rejects")
        self.assertIn("error", mod.record(db, "nope", "hard"))
        self.assertIn("error", mod.record(db, "m:add", "medium"))


if __name__ == "__main__":
    unittest.main()
