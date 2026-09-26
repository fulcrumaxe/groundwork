"""Give-up reveal (I-158): surrender logs grade 0, answer after attempt."""
import sqlite3
import unittest

from test_web import make_module

from groundwork import reveal as rvmod


class RevealRequestTest(unittest.TestCase):
    def test_blank_plus_floor_is_reveal(self):
        self.assertTrue(rvmod.is_reveal_request("", 1))
        self.assertTrue(rvmod.is_reveal_request("   ", 1))

    def test_real_attempts_are_not_reveals(self):
        self.assertFalse(rvmod.is_reveal_request("Paris", 1))
        self.assertFalse(rvmod.is_reveal_request("", 3))
        self.assertFalse(rvmod.is_reveal_request("3", 3))
        self.assertFalse(rvmod.is_reveal_request("", 5))

    def test_bad_types_fail_closed_to_attempt(self):
        for bad in (None, 0, 5, ["x"], {"a": 1}):
            self.assertFalse(rvmod.is_reveal_request(bad, 1))
        self.assertFalse(rvmod.is_reveal_request("", None))
        self.assertFalse(rvmod.is_reveal_request("", "high"))


class RevealResultTest(unittest.TestCase):
    def test_always_grade_zero_fail(self):
        for card in ({"back": "Paris"}, {}, {"back": ""},
                     {"back": None}, None, "nope", 42):
            res = rvmod.reveal_result(card)
            self.assertFalse(res["pass"])
            self.assertEqual(res["score"], 0.0)
            self.assertEqual(res["grade"], 0)
            self.assertTrue(res["revealed"])
            self.assertIn("grade 0", res["feedback"].lower())

    def test_back_named_only_when_present(self):
        self.assertIn("Paris", rvmod.reveal_result({"back": "Paris"})["feedback"])
        self.assertNotIn("Answer:", rvmod.reveal_result({})["feedback"])
        self.assertNotIn("Answer:", rvmod.reveal_result(None)["feedback"])


class BackVisibleTest(unittest.TestCase):
    def test_answer_only_after_attempt(self):
        self.assertFalse(rvmod.back_visible(False))
        self.assertFalse(rvmod.back_visible(None))
        self.assertFalse(rvmod.back_visible(0))
        self.assertTrue(rvmod.back_visible(True))
        self.assertTrue(rvmod.back_visible(1))


class SectionTourTest(unittest.TestCase):
    def test_section_html_anchor(self):
        body = rvmod.section_html()
        self.assertIn(f"id='{rvmod.STATUS_ANCHOR}'", body)
        self.assertIn("is_reveal_request", body)
        self.assertIn("grade 0", body)

    def test_tour_entry_shape(self):
        e = rvmod.tour_entry()
        self.assertEqual("improvement", e["kind"])
        self.assertEqual(rvmod.STATUS_ANCHOR, e["anchor"])
        for key in ("id", "title", "blurb", "path", "anchor"):
            self.assertTrue(e[key])
        self.assertTrue(e["path"].startswith("/"))


class EffectTest(unittest.TestCase):
    def test_giveup_logs_grade_zero_on_any_type(self):
        tmp, db, server, out = make_module("reveal live")
        due = server.tool_list_due_reviews({"limit": 5})["due"]
        self.assertTrue(due)
        seen_types = set()
        for card in due:
            res = server.submit_review(card["id"], "", 1)
            self.assertFalse(res["result"]["pass"])
            self.assertEqual(res["grade"], 0)
            self.assertIn("Gave up", res["result"]["feedback"])
            seen_types.add(str(card.get("exercise_type")))
            con = sqlite3.connect(db)
            try:
                grade = con.execute(
                    "SELECT grade FROM reviews WHERE card_id=? ORDER BY rowid DESC LIMIT 1",
                    (card["id"],)).fetchone()[0]
            finally:
                con.close()
            self.assertEqual(grade, 0)
        # The fixture deals recall + explain types: the fix covers
        # non-recall surrenders that used to log grade 1.
        self.assertGreaterEqual(len(seen_types), 2)

    def test_real_attempt_still_grades_normally(self):
        tmp, db, server, out = make_module("reveal normal")
        due = server.tool_list_due_reviews({"limit": 5})["due"]
        ones = [c for c in due if str(c.get("exercise_type")) == "1"]
        self.assertTrue(ones)
        res = server.submit_review(ones[0]["id"], "4", 3)
        self.assertEqual(res["grade"], 4)
        self.assertTrue(res["result"]["pass"])


if __name__ == "__main__":
    unittest.main()
