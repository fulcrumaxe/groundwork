"""One-click practice-similar variants: failed shuffle cards mint a sibling (I-191)."""
import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from groundwork import db as dbmod
from groundwork import exercises as exmod
from groundwork import mcp as mcplib
from groundwork import similar as mod

PARSONS = {"lines": ["total = a + b", "def add(a, b):", "return total",
                     "result = add(2, 3)"],
           "solution": ["def add(a, b):", "total = a + b", "return total",
                        "result = add(2, 3)"],
           "tests": ""}
CHOICE = {"func": "add", "signature": "add(a, b)",
          "choices": ["add(a, b)", "add(b, a)", "add(...)"],
          "answer": "add(a, b)"}
MATCH = {"pairs": [["add", "calc.py"], ["render", "web.py"],
                   ["grade", "ex.py"]],
         "left": ["grade", "add", "render"],
         "right": ["calc.py", "ex.py", "web.py"],
         "key": {"0": "B", "1": "A", "2": "C"}}


def _fresh_db():
    tmp = Path(tempfile.mkdtemp(prefix="gw-similar-"))
    db = str(tmp / "sim.db")
    dbmod.init_db(db)
    con = sqlite3.connect(db)
    try:
        con.execute("INSERT INTO modules(id, repo, task_summary)"
                    " VALUES(?,?,?)", ("m1", str(tmp), "similar fixture"))
        con.execute("INSERT INTO concepts(id, module_id, name, kind, file,"
                    " line) VALUES(?,?,?,?,?,?)",
                    ("m1:add", "m1", "add", "function", "calc.py", 1))
        con.commit()
    finally:
        con.close()
    return db


def _insert_card(db, cid, etype, payload):
    con = sqlite3.connect(db)
    try:
        con.execute("INSERT INTO cards(id, concept_id, exercise_type, front,"
                    " back, payload) VALUES(?,?,?,?,?,?)",
                    (cid, "m1:add", str(etype), f"front of {cid}",
                     f"back of {cid}", json.dumps(payload)))
        con.commit()
    finally:
        con.close()


def _card_row(db, cid):
    con = sqlite3.connect(db)
    try:
        con.row_factory = sqlite3.Row
        return dict(con.execute("SELECT * FROM cards WHERE id=?",
                                (cid,)).fetchone())
    finally:
        con.close()


def _card_count(db):
    con = sqlite3.connect(db)
    try:
        return con.execute("SELECT COUNT(*) FROM cards").fetchone()[0]
    finally:
        con.close()


class EligibleTest(unittest.TestCase):
    def test_choice_order_match_eligible(self):
        self.assertTrue(mod.eligible("7", CHOICE))
        self.assertTrue(mod.eligible(11, PARSONS))
        self.assertTrue(mod.eligible("30", MATCH))

    def test_order_free_types_ineligible(self):
        for t in ("1", "2", "5", "6", "22", "25", "99"):
            self.assertFalse(mod.eligible(t, CHOICE), t)
            self.assertFalse(mod.eligible(t, PARSONS), t)

    def test_degenerate_payloads_ineligible(self):
        self.assertFalse(mod.eligible("7", {"choices": ["only"]}))
        self.assertFalse(mod.eligible("7", {"choices": ["x", "x"]}))
        self.assertFalse(mod.eligible("11", {"lines": ["a"], "solution": ["a"]}))
        self.assertFalse(mod.eligible("11", {"lines": ["a", "b"]}))
        self.assertFalse(mod.eligible("30", {"pairs": [], "left": [], "right": []}))
        self.assertFalse(mod.eligible("11", None))
        self.assertFalse(mod.eligible(None, None))


class VariantPayloadTest(unittest.TestCase):
    def test_choice_keeps_answer_new_order(self):
        vp = mod.variant_payload("18", CHOICE, "seed-1")
        self.assertEqual(sorted(vp["choices"]), sorted(CHOICE["choices"]))
        self.assertNotEqual(vp["choices"], CHOICE["choices"])
        self.assertEqual(vp["answer"], "add(a, b)")
        self.assertEqual(vp["signature"], "add(a, b)")

    def test_order_keeps_solution_new_lines(self):
        vp = mod.variant_payload(11, PARSONS, "seed-2")
        self.assertEqual(vp["solution"], PARSONS["solution"])
        self.assertEqual(sorted(vp["lines"]), sorted(PARSONS["lines"]))
        self.assertNotEqual(vp["lines"], PARSONS["lines"])
        self.assertEqual(vp["tests"], "")

    def test_match_rekeys_consistently(self):
        vp = mod.variant_payload("30", MATCH, "seed-3")
        self.assertEqual(vp["pairs"], MATCH["pairs"])
        self.assertNotEqual((vp["left"], vp["right"]),
                            (MATCH["left"], MATCH["right"]))
        for i, a in enumerate(vp["left"]):
            want = next(b for aa, b in vp["pairs"] if aa == a)
            self.assertEqual(vp["key"][str(i)],
                             chr(ord("A") + vp["right"].index(want)))

    def test_shuffle_guarantee_across_seeds(self):
        for n in range(25):
            vp = mod.variant_payload("7", CHOICE, f"m1:ex001~sim{n}")
            self.assertNotEqual(vp["choices"], CHOICE["choices"])

    def test_same_seed_stable(self):
        self.assertEqual(mod.variant_payload("7", CHOICE, "s"),
                         mod.variant_payload("7", CHOICE, "s"))

    def test_ineligible_gives_none(self):
        self.assertIsNone(mod.variant_payload("22", {"answer": "A"}, "s"))
        self.assertIsNone(mod.variant_payload("1", {}, "s"))
        self.assertIsNone(mod.variant_payload("7", {"choices": ["x"]}, "s"))
        self.assertIsNone(mod.variant_payload("7", None, "s"))


class MintTest(unittest.TestCase):
    def test_mint_inserts_due_sibling(self):
        db = _fresh_db()
        _insert_card(db, "m1:ex001", 11, PARSONS)
        con = dbmod.connect(db)
        try:
            vid = mod.mint_variant(con, _card_row(db, "m1:ex001"))
            con.commit()
        finally:
            con.close()
        self.assertEqual(vid, "m1:ex001~sim1")
        sib = _card_row(db, vid)
        self.assertEqual(sib["concept_id"], "m1:add")
        self.assertEqual(sib["exercise_type"], "11")
        self.assertEqual(sib["front"], "front of m1:ex001")
        payload = json.loads(sib["payload"])
        self.assertEqual(payload["solution"], PARSONS["solution"])
        self.assertNotEqual(payload["lines"], PARSONS["lines"])
        due = [c["id"] for c in
               mcplib.MCPServer(db).tool_list_due_reviews({"limit": 100})["due"]]
        self.assertIn(vid, due)

    def test_reuse_outstanding_no_growth(self):
        db = _fresh_db()
        _insert_card(db, "m1:ex001", 7, CHOICE)
        con = dbmod.connect(db)
        try:
            first = mod.mint_variant(con, _card_row(db, "m1:ex001"))
            con.commit()
            second = mod.mint_variant(con, _card_row(db, "m1:ex001"))
            con.commit()
        finally:
            con.close()
        self.assertEqual((first, second),
                         ("m1:ex001~sim1", "m1:ex001~sim1"))
        self.assertEqual(_card_count(db), 2)

    def test_reviewed_sibling_allows_next(self):
        db = _fresh_db()
        _insert_card(db, "m1:ex001", 7, CHOICE)
        con = dbmod.connect(db)
        try:
            first = mod.mint_variant(con, _card_row(db, "m1:ex001"))
            con.execute("INSERT INTO reviews(card_id, grade) VALUES(?,?)",
                        (first, 5))
            con.commit()
            second = mod.mint_variant(con, _card_row(db, "m1:ex001"))
            con.commit()
        finally:
            con.close()
        self.assertEqual(second, "m1:ex001~sim2")

    def test_ineligible_mints_nothing(self):
        db = _fresh_db()
        _insert_card(db, "m1:ex001", 1, {"question": "q"})
        con = dbmod.connect(db)
        try:
            self.assertIsNone(mod.mint_variant(con, _card_row(db, "m1:ex001")))
            self.assertIsNone(mod.mint_variant(con, {"id": ""}))
        finally:
            con.close()
        self.assertEqual(_card_count(db), 1)


class OfferTest(unittest.TestCase):
    def test_pass_renders_legacy(self):
        db = _fresh_db()
        _insert_card(db, "m1:ex001", 11, PARSONS)
        con = dbmod.connect(db)
        try:
            self.assertEqual(mod.offer_html(con, _card_row(db, "m1:ex001"),
                                            True, "m1"), "")
        finally:
            con.close()
        self.assertEqual(_card_count(db), 1)

    def test_fail_links_variant_anchor(self):
        db = _fresh_db()
        _insert_card(db, "m1:ex001", 11, PARSONS)
        con = dbmod.connect(db)
        try:
            html_out = mod.offer_html(con, _card_row(db, "m1:ex001"),
                                      False, "m1")
            con.commit()
        finally:
            con.close()
        self.assertIn("Practice a similar card", html_out)
        self.assertIn("/modules/m1#card-m1-ex001-sim1", html_out)

    def test_fail_without_module_falls_back_to_queue(self):
        db = _fresh_db()
        _insert_card(db, "m1:ex001", 7, CHOICE)
        con = dbmod.connect(db)
        try:
            html_out = mod.offer_html(con, _card_row(db, "m1:ex001"), False)
            con.commit()
        finally:
            con.close()
        self.assertIn("href='/due'", html_out)

    def test_garbage_never_raises(self):
        self.assertEqual(mod.offer_html(None, None, False), "")
        self.assertIn("href='/due'", mod.link_html(None, None))
        self.assertEqual(mod.variant_id("c", 1), "c~sim1")


class GradeEquivalenceTest(unittest.TestCase):
    def test_variant_solution_order_passes(self):
        vp = mod.variant_payload(11, PARSONS, "m1:ex001~sim1")
        ex = {"id": "v", "type": 11, "front": "f", "back": "b",
              "payload": vp}
        idx = [str(vp["lines"].index(s)) for s in vp["solution"]]
        self.assertTrue(exmod.grade(ex, " ".join(idx))["pass"])

    def test_variant_choice_answer_passes(self):
        vp = mod.variant_payload("7", CHOICE, "m1:ex002~sim1")
        ex = {"id": "v", "type": 7, "front": "f", "back": "b",
              "payload": vp}
        self.assertTrue(exmod.grade(ex, "add(a, b)")["pass"])
        self.assertFalse(exmod.grade(ex, "add(b, a)")["pass"])


class WireIntegrationTest(unittest.TestCase):
    """Needs the parent wire: submit_review mints + web.py joins similar."""

    def test_failed_parsons_offers_sibling(self):
        db = _fresh_db()
        _insert_card(db, "m1:ex001", 11, PARSONS)
        server = mcplib.MCPServer(db)
        out = server.submit_review("m1:ex001", "3 2 1 0", 3)
        self.assertFalse(out["result"]["pass"])
        self.assertIn("card-m1-ex001-sim1", out.get("similar", ""))
        self.assertIn("Practice a similar card", out.get("similar", ""))
        self.assertEqual(_card_count(db), 2)

    def test_passed_card_offers_nothing(self):
        db = _fresh_db()
        _insert_card(db, "m1:ex001", 11, PARSONS)
        server = mcplib.MCPServer(db)
        vp = PARSONS
        idx = [str(vp["lines"].index(s)) for s in vp["solution"]]
        out = server.submit_review("m1:ex001", " ".join(idx), 4)
        self.assertTrue(out["result"]["pass"])
        self.assertEqual(out.get("similar", ""), "")
        self.assertEqual(_card_count(db), 1)

    def test_failed_recall_offers_nothing(self):
        db = _fresh_db()
        _insert_card(db, "m1:ex001", 1, {"question": "q", "answer": "a"})
        server = mcplib.MCPServer(db)
        out = server.submit_review("m1:ex001", "1", 2)
        self.assertFalse(out["result"]["pass"])
        self.assertEqual(out.get("similar", ""), "")
        self.assertEqual(_card_count(db), 1)


class PageTest(unittest.TestCase):
    def test_section_and_tour(self):
        html_out = mod.section_html()
        self.assertIn(mod.STATUS_ANCHOR, html_out)
        self.assertIn("Practice a similar card", html_out)
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["path"], "/status")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)
        self.assertEqual(entry["id"], "practice-similar")

    def test_source_ascii_only(self):
        src = (Path(__file__).resolve().parent.parent / "groundwork"
               / "similar.py").read_text(encoding="utf-8")
        self.assertTrue(all(ord(ch) < 128 for ch in src))
        self.assertLessEqual(src.count("\n") + 1, 350)


if __name__ == "__main__":
    unittest.main()
