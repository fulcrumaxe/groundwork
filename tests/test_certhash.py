"""Certificates with verification hashes (F-180)."""
import html as htmlmod
import re
import unittest

from groundwork import certhash as mod

from test_web import handler_for, make_module  # noqa: F401 -- handler_for pins harness


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


def _cert():
    return {"pack": "abc123", "summary": "Test pack",
            "owned": 5, "total": 5, "issued": "2026-09-20T10:00:00Z"}


class HashTest(unittest.TestCase):
    def test_digest_stable_64hex(self):
        body = mod.canonical(mod.claims_for(_cert()))
        d1, d2 = mod.digest(body), mod.digest(body)
        self.assertEqual(d1, d2)
        self.assertEqual(len(d1), 64)
        int(d1, 16)

    def test_issue_verify_round_trip(self):
        ok, reason = mod.verify_block(mod.issue_block(_cert()))
        self.assertTrue(ok)
        self.assertIn("matches", reason)

    def test_tampered_claims_fail(self):
        block = mod.issue_block(_cert()).replace("owned:5", "owned:50")
        ok, reason = mod.verify_block(block)
        self.assertFalse(ok)
        self.assertIn("do not match", reason)

    def test_tampered_hash_fails(self):
        lines = mod.issue_block(_cert()).splitlines()
        lines[-1] = "hash:" + "0" * 64
        ok, _ = mod.verify_block("\n".join(lines) + "\n")
        self.assertFalse(ok)

    def test_malformed_never_raises(self):
        for bad in (None, "", "hello", "GW-CERT/1\n", 123,
                    "GW-CERT/1\npack:x\nhash:00\n",
                    mod.issue_block(_cert()).replace("GW-CERT/1", "GW-X/9")):
            ok, reason = mod.verify_block(bad)
            self.assertFalse(ok)
            self.assertTrue(reason)

    def test_multiline_summary_round_trips(self):
        cert = _cert()
        cert["summary"] = "line one\n  line   two"
        ok, _ = mod.verify_block(mod.issue_block(cert))
        self.assertTrue(ok)


class SectionTest(unittest.TestCase):
    def test_empty_db_to_earn(self):
        _tmp, db, _s, _out = make_module("certhash empty")
        body = mod.section_html(db)
        self.assertIn("cert-hashes", body)
        self.assertIn("No verifiable certificates yet", body)
        self.assertIn("certcheck", body)

    def test_full_pack_issues_checkable_block(self):
        _tmp, db, _s, _out = make_module("certhash full")
        _own(db, _cid(db), "2026-09-20T10:00:00Z")
        body = mod.section_html(db)
        self.assertIn("Verifiable certificate", body)
        self.assertIn("sha256", body)
        self.assertIn("GW-CERT/1", body)
        m = re.search(r"<pre>(.*?)</pre>", body, re.S)
        self.assertIsNotNone(m)
        ok, _ = mod.verify_block(htmlmod.unescape(m.group(1)))
        self.assertTrue(ok)

    def test_query_verdict_match(self):
        _tmp, db, _s, _out = make_module("certhash verdict")
        _own(db, _cid(db), "2026-09-20T10:00:00Z")
        block = mod.issue_block(_cert())
        body = mod.section_html(db, {"certcheck": [block]})
        self.assertIn("cert-verdict", body)
        self.assertIn("matches its hash", body)

    def test_query_verdict_mismatch(self):
        _tmp, db, _s, _out = make_module("certhash mismatch")
        bad = mod.issue_block(_cert()).replace("owned:5", "owned:9")
        body = mod.section_html(db, {"certcheck": [bad]})
        self.assertIn("cert-verdict", body)
        self.assertIn("do not match", body)

    def test_blank_query_no_verdict(self):
        _tmp, db, _s, _out = make_module("certhash blank")
        body = mod.section_html(db, {"certcheck": ["  "]})
        self.assertNotIn("cert-verdict", body)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.cert_claims("/nonexistent.db"), [])
        self.assertIn("cert-hashes", mod.section_html("/nonexistent.db"))
        self.assertIn("cert-hashes", mod.section_html("/nonexistent.db", "x"))
        self.assertIn("cert-hashes",
                      mod.section_html("/nonexistent.db", {"certcheck": None}))

    def test_sibling_bytes_unchanged(self):
        from groundwork import teachcert as certmod
        _tmp, db, _s, _out = make_module("certhash legacy")
        _own(db, _cid(db), "2026-09-20T10:00:00Z")
        legacy = certmod.section_html(db)
        self.assertIn("Teaching certificate", legacy)
        self.assertNotIn("cert-hashes", legacy)
        self.assertNotIn("sha256", legacy)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "feature")
        self.assertEqual(entry["path"], "/reviews")
        self.assertEqual(entry["anchor"], "cert-hashes")


class CallerEffectTest(unittest.TestCase):
    def test_history_renders_anchor(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("certhash history")
        body = histmod.history_html(db)
        self.assertIn("cert-hashes", body)
        self.assertIn("teaching-certificates", body)

    def test_history_lists_checkable_certificate(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("certhash listed")
        _own(db, _cid(db), "2026-09-20T10:00:00Z")
        body = histmod.history_html(db)
        self.assertIn("Verifiable certificate", body)

    def test_history_query_renders_verdict(self):
        from groundwork import history as histmod
        _tmp, db, _s, _out = make_module("certhash wired")
        body = histmod.history_html(db, {"certcheck": [mod.issue_block(_cert())]})
        self.assertIn("cert-verdict", body)
        self.assertIn("matches its hash", body)


if __name__ == "__main__":
    unittest.main()
