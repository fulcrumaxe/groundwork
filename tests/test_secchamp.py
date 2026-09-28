"""Security-champions track per area (F-190)."""
import unittest

from groundwork import db as dbmod
from groundwork import secchamp as mod

from test_web import handler_for, make_module


def _two_services(db, mid):
    """Security cards (49/50/51) in payments/, a recall card in shop/."""
    con = dbmod.connect(db)
    try:
        cid1 = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        con.execute("UPDATE concepts SET file='payments/api.py', name='charge'"
                    " WHERE id=?", (cid1,))
        con.execute("DELETE FROM cards WHERE concept_id=?", (cid1,))
        for i, t in enumerate(("49", "50", "51")):
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
                " VALUES(?, ?, ?, ?, 'why')",
                (f"{cid1}:s{i}", cid1, t, f"sec front {t}"))
        cid2 = f"{mid}:shop-fn"
        con.execute(
            "INSERT INTO concepts(id, module_id, name, file)"
            " VALUES(?, ?, 'browse', 'shop/web.py')",
            (cid2, mid))
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
            " VALUES(?, ?, '1', 'shop front', 'why')",
            (f"{cid2}:c1", cid2))
        con.commit()
    finally:
        con.close()
    return cid1


class ServiceScopeTest(unittest.TestCase):
    def test_normalize(self):
        self.assertEqual(mod.normalize_scope("payments\\api"), "payments/api")
        self.assertEqual(mod.normalize_scope("./x/"), "x")
        self.assertEqual(mod.normalize_scope(None), "")
        self.assertEqual(mod.normalize_scope(5), "")

    def test_match_boundaries(self):
        self.assertTrue(mod.match("", "anything.py"))
        self.assertTrue(mod.match("payments", "payments/api.py"))
        self.assertTrue(mod.match("payments/api", "payments/api.py"))
        self.assertTrue(mod.match("payments/api.py", "payments/api.py"))
        self.assertFalse(mod.match("payments/ap", "payments/api.py"))
        self.assertFalse(mod.match("shop", "payments/api.py"))
        self.assertFalse(mod.match("payments", ""))

    def test_match_hostile_never_raises(self):
        self.assertFalse(mod.match("payments", None))
        self.assertEqual(mod.match(None, None), True)


class PickTrackTest(unittest.TestCase):
    def test_gathers_only_security_types_in_service(self):
        tmp, db, server, out = make_module("secchamp pick mod")
        _two_services(db, out["module_id"])
        picks = mod.pick_track(db, "payments")
        self.assertEqual(len(picks), 3)
        self.assertEqual({p["exercise_type"] for p in picks}, {"49", "50", "51"})
        self.assertEqual({p["type_name"] for p in picks},
                         {"threat-model", "secret-scan", "input-validation"})
        self.assertTrue(all(p["name"] == "charge" for p in picks))
        self.assertEqual(mod.pick_track(db, "shop"), [])

    def test_weakest_first_unknown_surfaces(self):
        tmp, db, server, out = make_module("secchamp order mod")
        cid1 = _two_services(db, out["module_id"])
        con = dbmod.connect(db)
        try:
            con.execute("INSERT INTO reviews(card_id, grade, confidence)"
                        " VALUES(?, 5, 5)", (f"{cid1}:s0",))
            con.execute("INSERT INTO reviews(card_id, grade, confidence)"
                        " VALUES(?, 5, 5)", (f"{cid1}:s0",))
            con.commit()
        finally:
            con.close()
        picks = mod.pick_track(db, "payments")
        self.assertEqual([p["exercise_type"] for p in picks], ["50", "51", "49"])
        self.assertIn("no attempts yet", picks[0]["reason"])
        self.assertIn("avg 5.0", picks[-1]["reason"])

    def test_hostile_inputs_yield_empty(self):
        self.assertEqual(mod.pick_track("/no/such.db", "payments"), [])
        tmp, db, server, out = make_module("secchamp hostile mod")
        self.assertEqual(mod.pick_track(db, None), mod.pick_track(db, ""))
        self.assertEqual(mod.pick_track(db, "payments", size="bogus"),
                         mod.pick_track(db, "payments"))


class ProgressTest(unittest.TestCase):
    def test_owned_proofs_shape(self):
        tmp, db, server, out = make_module("secchamp progress mod")
        _two_services(db, out["module_id"])
        self.assertEqual(mod.track_progress(db, "payments"),
                         {"total": 1, "owned": 0, "due": 3})
        self.assertEqual(mod.track_progress(db, "nope"),
                         {"total": 0, "owned": 0, "due": 0})

    def test_bad_db_is_zeros(self):
        self.assertEqual(mod.track_progress("/no/such.db", "payments"),
                         {"total": 0, "owned": 0, "due": 0})


class CallerEffectTest(unittest.TestCase):
    def test_scope_renders_track_box(self):
        """Behavioral effect: ?scope= adds the scoped track to Due."""
        tmp, db, server, out = make_module("secchamp effect mod")
        _two_services(db, out["module_id"])
        body = handler_for(db).due_html(scope="payments")
        self.assertIn("id='secchamp-track'", body)
        self.assertIn("Security-champions track: payments", body)
        self.assertIn("0/1 track concepts owned", body)
        self.assertIn("threat-model", body)
        self.assertIn("secret-scan", body)
        self.assertIn("input-validation", body)
        # ?scope= also narrows the queue itself (ramppack precedent):
        # the other area's card is out of the queue, not just the box.
        self.assertNotIn("shop front", body)

    def test_unknown_scope_is_honest_notice(self):
        tmp, db, server, out = make_module("secchamp unknown mod")
        _two_services(db, out["module_id"])
        body = handler_for(db).due_html(scope="nope")
        self.assertIn("id='secchamp-track'", body)
        self.assertIn("Unknown scope", body)
        self.assertIn("no files match", body)

    def test_no_scope_is_legacy(self):
        """Fallback pin: unscoped Due bytes carry no track."""
        tmp, db, server, out = make_module("secchamp legacy mod")
        _two_services(db, out["module_id"])
        body = handler_for(db).due_html()
        self.assertNotIn("secchamp-track", body)
        self.assertIn("sec front 49", body)
        self.assertIn("shop front", body)
        self.assertEqual(mod.track_html(db, ""), "")
        self.assertEqual(mod.track_html(db, None), "")


class StatusTourTest(unittest.TestCase):
    def test_status_anchor(self):
        self.assertIn("id='status-b29-secchamp'", mod.section_html())
        tmp, db, server, out = make_module("secchamp status mod")
        _two_services(db, out["module_id"])
        self.assertIn("3 security cards", mod.section_html(db))

    def test_tour_entry(self):
        t = mod.tour_entry()
        self.assertEqual(t["id"], "secchamp-track")
        self.assertEqual(t["kind"], "feature")
        self.assertEqual(t["path"], "/status")
        self.assertEqual(t["anchor"], "status-b29-secchamp")


if __name__ == "__main__":
    unittest.main()
