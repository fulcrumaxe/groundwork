"""Milestone moments: first Owned, 10th module, full coverage (F-107)."""
import unittest

from groundwork import db as dbmod
from groundwork import milestones as mod

from test_web import handler_for, make_module


def _own_fixture():
    tmp, db, server, out = make_module("milestones mod")
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES('milestones-c1', ?, '19', 'q', 'a')", (cid,))
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES('milestones-c1', 5, 4, '2026-01-02T10:00:00Z')")
        con.execute(
            "INSERT INTO reviews(card_id, grade, confidence, reviewed_at)"
            " VALUES('milestones-c1', 5, 4, '2026-01-05T10:00:00Z')")
        con.commit()
    finally:
        con.close()
    return tmp, db, server, out


class MomentsTest(unittest.TestCase):
    def test_empty_no_moments(self):
        _tmp, db, _s, _o = make_module("milestones empty")
        self.assertEqual(mod.moments(db), [])
        self.assertIn("No milestones yet", mod.section_html(db))

    def test_first_owned_dated_at_second_pass(self):
        _tmp, db, _s, _o = _own_fixture()
        ms = mod.moments(db)
        first = [m for m in ms if m["kind"] == "first-owned"]
        self.assertEqual(len(first), 1)
        self.assertEqual(first[0]["when"], "2026-01-05T10:00:00Z")

    def test_tenth_module_absent_when_few(self):
        _tmp, db, _s, _o = _own_fixture()
        kinds = [m["kind"] for m in mod.moments(db)]
        self.assertNotIn("tenth-module", kinds)

    def test_tenth_module_dated(self):
        _tmp, db, _s, _o = make_module("milestones tenth")
        con = dbmod.connect(db)
        try:
            cid = con.execute(
                "SELECT id FROM cards LIMIT 1").fetchone()[0]
            for i in range(mod.TENTH_MODULE_N):
                mid = f"tenth-m{i}"
                con.execute(
                    "INSERT INTO modules(id, repo) VALUES(?, 'r')", (mid,))
                con.execute(
                    "INSERT INTO concepts(id, module_id, name)"
                    f" VALUES('tenth-c{i}', ?, 'c')", (mid,))
                con.execute(
                    "INSERT INTO cards(id, concept_id, exercise_type)"
                    f" VALUES('tenth-k{i}', 'tenth-c{i}', '1')")
                con.execute(
                    "INSERT INTO reviews(card_id, grade, reviewed_at)"
                    " VALUES(?, 4, ?)", (f"tenth-k{i}",
                                         f"2026-02-{i + 1:02d}T10:00:00Z"))
            con.commit()
        finally:
            con.close()
        ms = mod.moments(db)
        tenth = [m for m in ms if m["kind"] == "tenth-module"]
        self.assertEqual(len(tenth), 1)
        # The fixture module has no reviews, so the 10 inserted modules
        # are all there is: the 10th falls on 2026-02-10.
        self.assertTrue(tenth[0]["when"].startswith("2026-02-10"))

    def test_full_repo_when_single_module_owned(self):
        _tmp, db, _s, _o = _own_fixture()
        ms = mod.moments(db)
        full = [m for m in ms if m["kind"] == "full-repo"]
        self.assertEqual(len(full), 1)
        self.assertIn("Full coverage", full[0]["label"])

    def test_hostile_empty(self):
        self.assertEqual(mod.moments(None), [])
        self.assertEqual(mod.owned_dates("/no/such.sqlite"), {})
        self.assertEqual(mod.module_first_dates(None), {})

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "milestone-moments", "kind": "feature",
            "title": "Milestone moments",
            "blurb": ("First Owned, tenth module, full coverage — the "
                      "dates that mattered."),
            "path": "/reviews", "anchor": "milestones"})


class CallerEffectTest(unittest.TestCase):
    def test_history_carries_milestones(self):
        _tmp, db, server, _o = make_module("milestones caller")
        card = server.tool_list_due_reviews({"limit": 1})["due"][0]
        server.submit_review(card["id"], "5", 4)
        body = handler_for(db).history_html()
        self.assertIn("id='milestones'", body)

    def test_empty_history_still_anchored(self):
        _tmp, db, _s, _o = make_module("milestones empty2")
        body = handler_for(db).history_html()
        self.assertIn("id='milestones'", body)


if __name__ == "__main__":
    unittest.main()
