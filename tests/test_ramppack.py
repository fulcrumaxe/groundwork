"""Contractor ramp packs scoped to one work area (F-162)."""
import unittest

from groundwork import db as dbmod
from groundwork import ramppack as mod

from test_web import handler_for, make_module


def _two_files(db, mid):
    """Two concepts in two files, one due card each, distinct fronts."""
    con = dbmod.connect(db)
    try:
        cid1 = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        con.execute("UPDATE concepts SET file='groundwork/alpha.py'"
                    " WHERE id=?", (cid1,))
        con.execute("UPDATE cards SET front='alpha front'"
                    " WHERE concept_id=?", (cid1,))
        cid2 = f"{mid}:beta-fn"
        con.execute(
            "INSERT INTO concepts(id, module_id, name, file)"
            " VALUES(?, ?, 'beta', 'groundwork/beta.py')",
            (cid2, mid))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES(?, ?, '1', 'beta front', 'why')",
            (f"{cid2}:c1", cid2))
        con.commit()
    finally:
        con.close()


class ScopeSemanticsTest(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(mod.normalize_scope("groundwork\\cards"), "groundwork/cards")
        self.assertEqual(mod.normalize_scope("./x/"), "x")
        self.assertEqual(mod.normalize_scope(None), "")
        self.assertEqual(mod.normalize_scope(5), "")

    def test_match_boundaries(self):
        self.assertTrue(mod.match("", "anything.py"))
        self.assertTrue(mod.match("groundwork", "groundwork/cards.py"))
        self.assertTrue(mod.match("groundwork/cards", "groundwork/cards.py"))
        self.assertTrue(mod.match("groundwork/cards.py", "groundwork/cards.py"))
        self.assertFalse(mod.match("groundwork/card", "groundwork/cards.py"))
        self.assertFalse(mod.match("tests", "groundwork/cards.py"))
        self.assertFalse(mod.match("groundwork", ""))

    def test_filter_due_pure(self):
        due = [{"id": "a", "concept_id": "c1"},
               {"id": "b", "concept_id": "c2"}]
        files = {"c1": "groundwork/alpha.py", "c2": "tests/x.py"}
        self.assertIs(mod.filter_due(due, files, ""), due)
        out = mod.filter_due(due, files, "groundwork")
        self.assertEqual([c["id"] for c in out], ["a"])
        self.assertEqual(mod.filter_due(due, files, "nope"), [])


class CallerEffectTest(unittest.TestCase):
    def test_scope_filters_due_queue(self):
        """Behavioral effect: scoped queue shows only in-scope cards."""
        tmp, db, server, out = make_module("ramppack mod")
        _two_files(db, out["module_id"])
        body = handler_for(db).due_html(scope="groundwork/alpha")
        self.assertIn("alpha front", body)
        self.assertNotIn("beta front", body)
        self.assertIn("id='ramppack-pack'", body)
        self.assertIn("0/1 owned", body)

    def test_no_scope_is_legacy(self):
        tmp, db, server, out = make_module("ramp legacy mod")
        _two_files(db, out["module_id"])
        body = handler_for(db).due_html()
        self.assertNotIn("id='ramppack-pack'", body)
        self.assertNotIn("?scope=", body)
        self.assertIn("alpha front", body)
        self.assertIn("beta front", body)

    def test_unknown_scope_falls_back_to_full_queue(self):
        tmp, db, server, out = make_module("ramppack unknown mod")
        _two_files(db, out["module_id"])
        body = handler_for(db).due_html(scope="nope/zone")
        self.assertIn("alpha front", body)
        self.assertIn("beta front", body)
        self.assertIn("Unknown scope", body)


class ShapeTest(unittest.TestCase):
    def test_section_html_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())
        tmp, db, server, out = make_module("ramppack status mod")
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html(db))

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("ramppack-pack", "feature",
                          "/status", mod.STATUS_ANCHOR))


if __name__ == "__main__":
    unittest.main()
