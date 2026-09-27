"""Gradebook export: your owned proofs as LMS-ready CSV (F-166)."""
import csv
import io
import unittest
from urllib.parse import unquote

from groundwork import db as dbmod
from groundwork import gradebook as mod
from groundwork import history as histmod
from groundwork import ownership as ownmod

from test_web import make_module


def _earn_owned(db):
    """One owned concept via two grade-5 modify/create reviews."""
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        card = con.execute(
            "SELECT id FROM cards WHERE concept_id=? LIMIT 1",
            (cid,)).fetchone()[0]
        con.execute("UPDATE cards SET exercise_type=? WHERE id=?",
                    (ownmod.ownership_types()[0], card))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at) VALUES(?, 5, 4, '2026-09-20T10:00:00Z')",
                (card,))
        con.commit()
    finally:
        con.close()


class CsvShapeTest(unittest.TestCase):
    def test_header_is_stable(self):
        self.assertEqual(mod.csv_text([]).splitlines()[0],
                         "concept,module,owned,owned_date,attempts,passes")

    def test_owned_row_yes_with_date(self):
        text = mod.csv_text([{"concept": "C", "module": "M",
                              "owned": True,
                              "owned_date": "2026-09-20T10:00:00Z",
                              "attempts": 2, "passes": 2}])
        rows = list(csv.reader(io.StringIO(text)))
        self.assertEqual(rows[1], ["C", "M", "yes",
                                  "2026-09-20T10:00:00Z", "2", "2"])

    def test_unowned_row_no_without_date(self):
        text = mod.csv_text([{"concept": "C", "module": "M",
                              "owned": False, "owned_date": "",
                              "attempts": 1, "passes": 0}])
        rows = list(csv.reader(io.StringIO(text)))
        self.assertEqual(rows[1], ["C", "M", "no", "", "1", "0"])

    def test_hostile_input_stays_valid_csv(self):
        text = mod.csv_text([None, "x", {}, {"concept": None,
                                             "owned": "truthy",
                                             "attempts": "3x",
                                             "passes": -2}])
        rows = list(csv.reader(io.StringIO(text)))
        self.assertEqual(rows[0], list(mod.HEADER))
        self.assertEqual(rows[-1], ["", "", "yes", "", "0", "0"])
        self.assertEqual(mod.csv_text(None).splitlines(),
                         [",".join(mod.HEADER)])

    def test_download_href_round_trips(self):
        text = mod.csv_text([{"concept": "a,b", "module": "M",
                              "owned": True, "owned_date": "d",
                              "attempts": 2, "passes": 1}])
        href = mod.download_href(text)
        self.assertTrue(href.startswith("data:text/csv;charset=utf-8,"))
        self.assertEqual(unquote(href.split(",", 1)[1]), text)


class RowsTest(unittest.TestCase):
    def test_fresh_db_all_unowned_no_dates(self):
        tmp, db, server, out = make_module("gradebook fresh mod")
        data = mod.rows(db)
        self.assertTrue(data)
        self.assertFalse(any(r["owned"] for r in data))
        self.assertTrue(all(r["owned_date"] == "" for r in data))
        self.assertTrue(all(r["attempts"] == 0 for r in data))
        self.assertTrue(all(r["passes"] == 0 for r in data))

    def test_earned_owned_carries_proof_date(self):
        tmp, db, server, out = make_module("gradebook owned mod")
        _earn_owned(db)
        data = mod.rows(db)
        owned = [r for r in data if r["owned"]]
        self.assertEqual(len(owned), 1)
        self.assertEqual(owned[0]["owned_date"],
                         "2026-09-20T10:00:00Z")
        self.assertEqual(owned[0]["attempts"], 2)
        self.assertEqual(owned[0]["passes"], 2)

    def test_gradebook_csv_matches_rows(self):
        tmp, db, server, out = make_module("gradebook csv mod")
        _earn_owned(db)
        parsed = list(csv.reader(io.StringIO(mod.gradebook_csv(db))))
        self.assertEqual(parsed[0], list(mod.HEADER))
        self.assertEqual(len(parsed), 1 + len(mod.rows(db)))


class CallerEffectTest(unittest.TestCase):
    def test_history_grows_gradebook_once_owned(self):
        """Behavioral effect: rendered History differs with live data."""
        tmp, db, server, out = make_module("gradebook live mod")
        before = histmod.history_html(db)
        self.assertIn("id='gradebook'", before)
        self.assertIn("No gradebook yet", before)
        self.assertNotIn("gradebook.csv", before)
        _earn_owned(db)
        after = histmod.history_html(db)
        self.assertIn("id='gradebook'", after)
        self.assertIn("gradebook.csv", after)
        self.assertIn("2026-09-20T10:00:00Z", after)
        self.assertIn("Copy-paste CSV", after)

    def test_fresh_db_placeholder_never_crashes(self):
        tmp, db, server, out = make_module("gradebook empty mod")
        body = histmod.history_html(db)
        self.assertIn("id='gradebook'", body)  # anchor-stable for tour gate


class ShapeTest(unittest.TestCase):
    def test_status_anchor(self):
        tmp, db, server, out = make_module("gradebook status mod")
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.status_html(db))

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("gradebook-export", "feature", "/reviews",
                          "gradebook"))


if __name__ == "__main__":
    unittest.main()
