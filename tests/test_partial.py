"""Per-blank partial-credit display for cloze (I-160)."""
import json
import sqlite3
import unittest

from test_web import make_module

from groundwork import partial as partialmod

CLOZE_PAYLOAD = {"blanks": [{"id": 0, "answers": ["timeout"]},
                            {"id": 1, "answers": ["retries"]},
                            {"id": 2, "answers": ["backoff"]}]}


def _cloze_card_id(db):
    con = sqlite3.connect(db)
    try:
        concept = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
        cid = "cloze-partial-1"
        con.execute(
            "INSERT OR REPLACE INTO cards(id, concept_id, exercise_type,"
            " front, back, payload) VALUES(?,?,?,?,?,?)",
            (cid, concept, "2", "Fill the blanks", "timeout retries backoff",
             json.dumps(CLOZE_PAYLOAD)))
        con.commit()
    finally:
        con.close()
    return cid


class PerBlankTest(unittest.TestCase):
    def test_names_passed_and_failed(self):
        rows = partialmod.per_blank(CLOZE_PAYLOAD, "0=timeout\n1=wrng\n2=backoff")
        self.assertEqual([r["passed"] for r in rows], [True, False, True])
        self.assertEqual([r["id"] for r in rows], [0, 1, 2])

    def test_whitespace_fold_matches_grader(self):
        payload = {"blanks": [{"id": 0, "answers": ["a  b"]}]}
        self.assertTrue(partialmod.per_blank(payload, "0=a   b")[0]["passed"])

    def test_ast_fallback_matches_grader(self):
        payload = {"blanks": [{"id": 0, "answers": ["x=1"]}]}
        self.assertTrue(partialmod.per_blank(payload, "0=x = 1")[0]["passed"])

    def test_single_blank_bare_answer(self):
        payload = {"answers": ["timeout"]}
        rows = partialmod.per_blank(payload, "timeout")
        self.assertEqual(len(rows), 1)
        self.assertTrue(rows[0]["passed"])

    def test_no_data_never_raises(self):
        self.assertEqual(partialmod.per_blank({}, "0=x"), [])
        self.assertEqual(partialmod.per_blank(None, "0=x"), [])
        self.assertEqual(partialmod.per_blank({"blanks": []}, "0=x"), [])


class SummaryLineTest(unittest.TestCase):
    def test_two_of_three(self):
        rows = [{"id": 0, "passed": True}, {"id": 1, "passed": False},
                {"id": 2, "passed": True}]
        self.assertEqual(partialmod.summary_line(rows),
                         "2 of 3 blanks right — blank 1 to retry.")

    def test_all_right(self):
        self.assertIn("All 2 blanks right.",
                      partialmod.summary_line([{"id": 0, "passed": True},
                                               {"id": 1, "passed": True}]))

    def test_empty_neutral(self):
        self.assertIn("No blank data", partialmod.summary_line([]))


class ChecklistHtmlTest(unittest.TestCase):
    def test_check_and_cross(self):
        rows = [{"id": 0, "passed": True, "given": "timeout",
                 "answers": ["timeout"]},
                {"id": 1, "passed": False, "given": "wrng",
                 "answers": ["retries"]}]
        body = partialmod.checklist_html(rows)
        self.assertIn("[+] Blank 0", body)
        self.assertIn("[!] Blank 1", body)
        self.assertIn("retries", body)

    def test_empty_is_empty_string(self):
        self.assertEqual(partialmod.checklist_html([]), "")

    def test_escapes_injection(self):
        rows = [{"id": 0, "passed": False, "given": "<script>",
                 "answers": ["<b>"]}]
        body = partialmod.checklist_html(rows)
        self.assertNotIn("<script>", body)
        self.assertNotIn("<b>", body)

    def test_status_demo_renders(self):
        body = partialmod.section_html()
        self.assertIn("status-b24-partial", body)
        self.assertIn("groundwork/partial.py", body)


class EffectTest(unittest.TestCase):
    def test_missed_cloze_names_passed_blanks(self):
        tmp, db, server, out = make_module("partial live")
        cid = _cloze_card_id(db)
        res = server.submit_review(cid, "0=timeout\n1=wrng\n2=backoff", 3)
        self.assertFalse(res["result"]["pass"])
        # Legacy line kept, per-blank verdict appended.
        self.assertIn("Blank(s)", res["result"]["feedback"])
        self.assertIn("2 of 3 blanks right", res["result"]["feedback"])

    def test_clean_cloze_legacy_byte_identical(self):
        tmp, db, server, out = make_module("partial clean")
        cid = _cloze_card_id(db)
        res = server.submit_review(cid, "0=timeout\n1=retries\n2=backoff", 3)
        self.assertTrue(res["result"]["pass"])
        self.assertEqual(res["result"]["feedback"], "All blanks correct.")


if __name__ == "__main__":
    unittest.main()
