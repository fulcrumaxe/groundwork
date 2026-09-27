"""Portable open badges 3.0 assertions (F-181)."""
import copy
import json
import unittest

from groundwork import openbadge as mod

from test_web import handler_for, make_module


def _own(db, cid, when):
    from groundwork import db as dbmod
    from groundwork import ownership as ownmod
    etype = ownmod.ownership_types()[0]
    con = dbmod.connect(db)
    try:
        card = con.execute(
            "SELECT id FROM cards WHERE concept_id=? LIMIT 1",
            (cid,)).fetchone()[0]
        con.execute("UPDATE cards SET exercise_type=? WHERE id=?",
                    (etype, card))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at) VALUES(?, 5, 4, ?)", (card, when))
        con.commit()
    finally:
        con.close()


def _cid(db):
    from groundwork import db as dbmod
    con = dbmod.connect(db)
    try:
        return con.execute("SELECT id FROM concepts").fetchall()[0]["id"]
    finally:
        con.close()


class ShapeTest(unittest.TestCase):
    def test_empty_db_no_assertions(self):
        _tmp, db, _s, _out = make_module("openbadge empty")
        self.assertEqual(mod.assertions(db), [])
        self.assertEqual(mod.assertion_json("m1", db), "")
        self.assertEqual(mod.section_html(db), "")

    def test_full_pack_assertion_shape(self):
        from groundwork import teachcert as certmod
        _tmp, db, _s, _out = make_module("openbadge full")
        _own(db, _cid(db), "2026-09-20T10:00:00Z")
        cert = certmod.eligible(db)[0]
        items = mod.assertions(db)
        self.assertEqual(len(items), 1)
        a = items[0]
        self.assertIn("https://purl.imsglobal.org/spec/ob/v3p0/context-3.0.3.json",
                      a["@context"])
        self.assertIn("OpenBadgeCredential", a["type"])
        self.assertEqual(a["issuer"]["name"], "Groundwork Library")
        subj = a["credentialSubject"]
        self.assertEqual(subj["id"], mod.recipient_id())
        self.assertEqual(subj["achievement"]["name"], cert["summary"])
        self.assertEqual(subj["achievement"]["id"],
                         "urn:groundwork:badgeclass:" + cert["pack"])
        self.assertEqual(a["validFrom"], cert["issued"])
        self.assertEqual(len(a["evidence"]), cert["total"])
        self.assertEqual(a["evidence"][0]["ownedOn"],
                         "2026-09-20T10:00:00Z")

    def test_recipient_hash_only_no_pii(self):
        _tmp, db, _s, _out = make_module("openbadge pii")
        _own(db, _cid(db), "2026-09-20T10:00:00Z")
        blob = mod.assertion_json(
            mod.assertions(db)[0]["credentialSubject"]["achievement"]
            ["id"].split(":")[-1], db)
        rid = mod.recipient_id()
        self.assertTrue(rid.startswith("urn:sha256:"))
        self.assertEqual(len(rid), len("urn:sha256:") + 64)
        self.assertEqual(rid, mod.recipient_id())  # deterministic
        lowered = blob.lower()
        self.assertNotIn("email", lowered)
        self.assertNotIn("mailto", lowered)

    def test_assertion_json_canonical(self):
        from groundwork import teachcert as certmod
        _tmp, db, _s, _out = make_module("openbadge canon")
        _own(db, _cid(db), "2026-09-20T10:00:00Z")
        pack = certmod.eligible(db)[0]["pack"]
        first = mod.assertion_json(pack, db)
        self.assertEqual(json.loads(first), mod.assertions(db)[0])
        self.assertEqual(first, mod.assertion_json(pack, db))
        self.assertEqual(mod.assertion_json("nope", db), "")


class VerifyTest(unittest.TestCase):
    def _fresh(self):
        _tmp, db, _s, _out = make_module("openbadge verify")
        _own(db, _cid(db), "2026-09-20T10:00:00Z")
        return db, copy.deepcopy(mod.assertions(db)[0])

    def test_fresh_assertion_verifies(self):
        db, a = self._fresh()
        self.assertTrue(mod.verify_assertion(a, db))

    def test_tampered_name_fails(self):
        db, a = self._fresh()
        a["credentialSubject"]["achievement"]["name"] = "Someone Elses Pack"
        self.assertFalse(mod.verify_assertion(a, db))

    def test_tampered_evidence_fails(self):
        db, a = self._fresh()
        a["evidence"] = a["evidence"][:-1]
        self.assertFalse(mod.verify_assertion(a, db))
        db2, _old = self._fresh()
        b = copy.deepcopy(mod.assertions(db2)[0])
        b["evidence"][0]["ownedOn"] = "2020-01-01T00:00:00Z"
        self.assertFalse(mod.verify_assertion(b, db2))

    def test_tampered_recipient_and_date_fail(self):
        db, a = self._fresh()
        a["credentialSubject"]["id"] = "urn:sha256:" + "0" * 64
        self.assertFalse(mod.verify_assertion(a, db))
        db2, _old = self._fresh()
        b = copy.deepcopy(mod.assertions(db2)[0])
        b["validFrom"] = "2020-01-01T00:00:00Z"
        self.assertFalse(mod.verify_assertion(b, db2))

    def test_hostile_fails_closed(self):
        db, _a = self._fresh()
        for bad in (None, "", "x", 5, [], {}):
            self.assertFalse(mod.verify_assertion(bad, db))
        self.assertFalse(mod.verify_assertion({"type": []}, db))
        self.assertFalse(
            mod.verify_assertion(mod.assertions(db)[0], "/nonexistent.db"))

    def test_hostile_never_raises(self):
        self.assertEqual(mod.assertions("/nonexistent.db"), [])
        self.assertEqual(mod.assertion_json("m1", "/nonexistent.db"), "")
        self.assertEqual(mod.section_html("/nonexistent.db"), "")
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())


class CallerEffectTest(unittest.TestCase):
    def test_history_serves_badges_when_eligible(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("openbadge served")
        _own(db, _cid(db), "2026-09-20T10:00:00Z")
        body = histmod.history_html(db)
        self.assertIn("open-badges", body)
        self.assertIn("Download assertion JSON", body)
        self.assertIn("OpenBadgeCredential", body)

    def test_history_byte_identical_without_eligible(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("openbadge legacy")
        body = histmod.history_html(db)
        self.assertNotIn("open-badges", body)
        self.assertNotIn("OpenBadgeCredential", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
