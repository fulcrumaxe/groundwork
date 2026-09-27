"""Syllabus week gates (F-175): later weeks unlock only on owned proofs."""
import json
import tempfile
import unittest
from pathlib import Path

from groundwork import db as dbmod
from groundwork import ownership as ownmod
from groundwork import syllabus as sylmod


SPEC = {"format": "groundwork-syllabus/1", "title": "T",
        "weeks": [["alpha"], ["beta"]]}


def make_db():
    tmp = Path(tempfile.mkdtemp(prefix="gw-syl-"))
    db = str(tmp / "syl.db")
    dbmod.init_db(db)
    con = dbmod.connect(db)
    con.execute("INSERT INTO modules(id, repo) VALUES('m1', 'r')")
    con.execute("INSERT INTO concepts(id, module_id, name, mastery)"
                " VALUES('m1:alpha', 'm1', 'alpha', 0.0)")
    con.execute("INSERT INTO concepts(id, module_id, name, mastery)"
                " VALUES('m1:beta', 'm1', 'beta', 0.0)")
    con.execute("INSERT INTO cards(id, concept_id, exercise_type)"
                " VALUES('c1', 'm1:alpha', '1')")
    con.execute("INSERT INTO cards(id, concept_id, exercise_type)"
                " VALUES('c2', 'm1:beta', '1')")
    con.commit()
    con.close()
    return db


def due_rows():
    return [{"id": "c1", "concept_id": "m1:alpha"},
            {"id": "c2", "concept_id": "m1:beta"}]


def own_alpha(db):
    otype = ownmod.ownership_types()[0]
    con = dbmod.connect(db)
    con.execute("UPDATE cards SET exercise_type=? WHERE id='c1'", (otype,))
    con.execute("INSERT INTO reviews(card_id, grade) VALUES('c1', 4)")
    con.execute("INSERT INTO reviews(card_id, grade) VALUES('c1', 5)")
    con.commit()
    con.close()


class ParseSpecTest(unittest.TestCase):
    def test_valid_dict_and_json_string(self):
        for spec in (SPEC, json.dumps(SPEC)):
            p = sylmod.parse_spec(spec)
            self.assertEqual(p["title"], "T")
            self.assertEqual(p["weeks"], [["alpha"], ["beta"]])

    def test_garbage_returns_empty(self):
        for bad in (None, 123, "", [], "{nope", {"weeks": "nope"},
                    {"format": "other/9", "weeks": [["a"]]}):
            self.assertEqual(sylmod.parse_spec(bad),
                             {"title": "", "weeks": []})

    def test_blanks_dupes_dropped_nonweek_rows_skipped(self):
        p = sylmod.parse_spec({"weeks": [["a", "", "a", " b "], "nope", []]})
        self.assertEqual(p["weeks"], [["a", "b"], []])

    def test_hostile_never_raises(self):
        self.assertEqual(sylmod.parse_spec(object()),
                         {"title": "", "weeks": []})


class WeekStatesTest(unittest.TestCase):
    def test_week1_open_week2_locked_until_proof(self):
        st = sylmod.week_states(SPEC)
        self.assertEqual([w["unlocked"] for w in st["weeks"]], [True, False])
        self.assertEqual(st["open"], 1)
        self.assertFalse(st["complete"])
        st = sylmod.week_states(SPEC, owned={"alpha"})
        self.assertEqual([w["unlocked"] for w in st["weeks"]], [True, True])
        self.assertEqual(st["open"], 2)

    def test_full_ownership_completes(self):
        st = sylmod.week_states(SPEC, owned={"alpha", "beta"})
        self.assertTrue(st["complete"])
        self.assertEqual(st["open"], 2)

    def test_mastery_counts_as_proof(self):
        st = sylmod.week_states(SPEC, mastery_of={"alpha": 0.9})
        self.assertTrue(st["weeks"][1]["unlocked"])
        st = sylmod.week_states(SPEC, mastery_of={"alpha": 0.5})
        self.assertFalse(st["weeks"][1]["unlocked"])

    def test_unknown_names_reported_never_locking(self):
        spec = {"weeks": [["nope"], ["alpha"]]}
        st = sylmod.week_states(spec, known={"alpha"})
        self.assertEqual(st["unknown"], ["nope"])
        self.assertTrue(st["weeks"][1]["unlocked"])
        self.assertEqual(sylmod.locked_names(spec, known={"alpha"}), set())

    def test_empty_and_hostile(self):
        st = sylmod.week_states(None)
        self.assertEqual((st["weeks"], st["open"], st["complete"]),
                         ([], 0, False))
        self.assertEqual(sylmod.locked_names(object()), set())


class GateDueTest(unittest.TestCase):
    def test_locked_week_cards_withheld(self):
        db = make_db()
        out = sylmod.gate_due(db, due_rows(), SPEC)
        self.assertEqual([c["id"] for c in out], ["c1"])

    def test_mastery_proof_releases_week(self):
        db = make_db()
        con = dbmod.connect(db)
        con.execute("UPDATE concepts SET mastery=0.9 WHERE id='m1:alpha'")
        con.commit()
        con.close()
        out = sylmod.gate_due(db, due_rows(), json.dumps(SPEC))
        self.assertEqual([c["id"] for c in out], ["c1", "c2"])

    def test_owned_proof_releases_week(self):
        db = make_db()
        own_alpha(db)
        out = sylmod.gate_due(db, due_rows(), SPEC)
        self.assertEqual([c["id"] for c in out], ["c1", "c2"])

    def test_no_spec_returns_same_list(self):
        db = make_db()
        for spec in (None, "", {}, {"weeks": []}):
            due = due_rows()
            self.assertIs(sylmod.gate_due(db, due, spec), due)

    def test_unknown_and_unlisted_pass_through(self):
        db = make_db()
        spec = {"weeks": [["nope"], ["alpha"]]}
        due = due_rows() + [{"id": "cx", "concept_id": "m9:zzz"}]
        out = sylmod.gate_due(db, due, spec)
        self.assertEqual([c["id"] for c in out], ["c1", "c2", "cx"])

    def test_empty_db_and_hostile_fail_open(self):
        tmp = Path(tempfile.mkdtemp(prefix="gw-syl-empty-"))
        db = str(tmp / "e.db")
        dbmod.init_db(db)
        due = due_rows()
        self.assertIs(sylmod.gate_due(db, due, SPEC), due)
        self.assertIs(sylmod.gate_due(db, "nope", SPEC), "nope")
        self.assertEqual(sylmod.gate_due(db, due, object()), due)


class BannerTest(unittest.TestCase):
    def test_empty_without_spec(self):
        db = make_db()
        for spec in (None, "", {}, {"weeks": []}, object()):
            self.assertEqual(sylmod.banner_html(db, spec), "")
            self.assertEqual(sylmod.states_html({}), "")

    def test_locked_banner_names_weeks_and_clears(self):
        html = sylmod.banner_html(make_db(), SPEC)
        self.assertIn("id='syllabus-gate'", html)
        self.assertIn("Week 1 of 2 open", html)
        self.assertIn("Week 1: 0/1 owned (open)", html)
        self.assertIn("Week 2: 0/1 owned (locked -- needs: beta)", html)
        self.assertIn("1 later-week concepts withheld", html)
        self.assertIn("<a href='/due'>Clear syllabus</a>", html)
        self.assertNotIn("<style", html.lower())

    def test_open_banner_and_unknown_note(self):
        db = make_db()
        own_alpha(db)
        html = sylmod.banner_html(db, SPEC)
        self.assertIn("Week 2 of 2 open", html)
        self.assertIn("0 later-week concepts withheld", html)
        html = sylmod.banner_html(db, {"weeks": [["nope"], ["alpha"]]})
        self.assertIn("never locking", html)

    def test_states_html_escapes_names(self):
        # Hostile name in a LOCKED week (open weeks render counts only).
        st = sylmod.week_states({"weeks": [["a"], ["<b>x</b>"]]})
        html = sylmod.states_html(st)
        self.assertNotIn("<b>", html)
        self.assertIn("&lt;b&gt;", html)


class StatusTourTest(unittest.TestCase):
    def test_section_html_anchor_and_demo(self):
        html = sylmod.section_html()
        self.assertIn("id='status-b28-syllabus'", html)
        self.assertIn("?syllabus=", html)
        self.assertIn("id='syllabus-gate'", html)

    def test_tour_entry_shape(self):
        entry = sylmod.tour_entry()
        self.assertEqual(entry["id"], "syllabus-gates")
        self.assertEqual(entry["kind"], "feature")
        self.assertTrue(entry["title"] and entry["blurb"])
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], "status-b28-syllabus")

    def test_shipped_source_ascii_no_placeholders(self):
        src = (Path(__file__).resolve().parent.parent
               / "groundwork" / "syllabus.py").read_text(encoding="utf-8")
        self.assertTrue(all(ord(c) < 128 for c in src))
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
