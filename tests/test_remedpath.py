"""Automatic remediation paths (F-100): failures queue prerequisites first."""
import json
import sqlite3
import unittest

from groundwork import db as dbmod
from groundwork import remedpath as mod

from test_web import make_module

MAP = {"X": ["A", "B", "C"],
       "Y": ["A", "X", "X", "Y"],
       "Z": ["P1", "P2", "P3", "P4", "P5"]}


def due_card(concept):
    return {"concept": concept, "front": "q", "back": "a"}


class PrereqsForTest(unittest.TestCase):
    def test_caps_at_three(self):
        self.assertEqual(mod.prereqs_for("Z", MAP), ["P1", "P2", "P3"])

    def test_unknown_or_bad_input_empty(self):
        self.assertEqual(mod.prereqs_for("nope", MAP), [])
        self.assertEqual(mod.prereqs_for("X", None), [])
        self.assertEqual(mod.prereqs_for("X", "nope"), [])
        self.assertEqual(mod.prereqs_for(None, MAP), [])


class MasteryTest(unittest.TestCase):
    def test_pass_threshold(self):
        self.assertTrue(mod.is_mastered("A", {"A": 3.0}))
        self.assertTrue(mod.is_mastered("A", {"A": 4.5}))
        self.assertFalse(mod.is_mastered("A", {"A": 2.9}))

    def test_missing_data_never_mastered(self):
        self.assertFalse(mod.is_mastered("A", {}))
        self.assertFalse(mod.is_mastered("A", None))
        self.assertFalse(mod.is_mastered("A", {"A": "x"}))
        self.assertFalse(mod.is_mastered("A", {"A": float("nan")}))
        self.assertFalse(mod.is_mastered(None, {"A": 5.0}))


class RemediationPathTest(unittest.TestCase):
    def test_fail_x_queues_three_prereqs_first(self):
        self.assertEqual(mod.remediation_path("X", MAP, {}),
                         ["A", "B", "C", "X"])

    def test_mastered_prereqs_skipped(self):
        path = mod.remediation_path("X", MAP, {"A": 4.0, "C": 5.0})
        self.assertEqual(path, ["B", "X"])

    def test_self_and_dupes_removed(self):
        path = mod.remediation_path("Y", MAP, {})
        self.assertEqual(path, ["A", "X", "Y"])
        self.assertEqual(path.count("X"), 1)

    def test_no_data_falls_back_to_failed_only(self):
        self.assertEqual(mod.remediation_path("X", {}), ["X"])
        self.assertEqual(mod.remediation_path("X", None), ["X"])
        self.assertEqual(mod.remediation_path("", MAP), [])
        self.assertEqual(mod.remediation_path(None, MAP), [])


class QueueRemediationTest(unittest.TestCase):
    def test_behavioral_effect_prereqs_prepended(self):
        due = [due_card("X"), due_card("Q")]
        out = mod.queue_remediation(due, ["X"], MAP, {})
        concepts = [c["concept"] for c in out]
        self.assertEqual(concepts[:3], ["A", "B", "C"])
        self.assertEqual(concepts[3:], ["X", "Q"])
        self.assertTrue(all(c["remedial"] for c in out[:3]))
        self.assertEqual(out[0]["remediation_for"], "X")

    def test_legacy_no_data_fallback_due_unchanged(self):
        due = [due_card("X")]
        self.assertEqual(mod.queue_remediation(due, ["X"], {}), due)
        self.assertEqual(mod.queue_remediation(due, ["X"], None), due)
        self.assertEqual(mod.queue_remediation(due, [], MAP), due)

    def test_no_duplicates_for_concepts_already_due(self):
        due = [due_card("X"), due_card("A")]
        out = mod.queue_remediation(due, ["X"], MAP, {})
        concepts = [c["concept"] for c in out]
        self.assertEqual(concepts.count("A"), 1)
        self.assertEqual(concepts[:2], ["B", "C"])

    def test_fail_closed_never_raises(self):
        res_none = mod.queue_remediation(None, ["X"], MAP, {})
        self.assertEqual([c["concept"] for c in res_none], ["A", "B", "C"])
        res = mod.queue_remediation("nope", ["X"], MAP, {})
        self.assertIsInstance(res, list)
        self.assertEqual([c["concept"] for c in res[:3]], ["A", "B", "C"])
        res = mod.queue_remediation([due_card("X")], ["X"], MAP, {},
                                    make_card="bad")
        self.assertEqual([c["concept"] for c in res][:3], ["A", "B", "C"])


class DescribePathTest(unittest.TestCase):
    def test_summary_names_prereqs_then_retry(self):
        text = mod.describe_path(["A", "B", "X"], "X")
        self.assertIn("A, B", text)
        self.assertIn("X", text)

    def test_empty_path(self):
        self.assertIn("No remediation path", mod.describe_path([]))

    def test_note_renders_empty_for_empty(self):
        self.assertEqual(mod.section_html([]), "")
        self.assertIn("remediation", mod.section_html(["A", "X"], "X"))

    def test_tour_entry_shape(self):
        self.assertEqual(mod.tour_entry(), {
            "id": "remediation-path", "kind": "feature",
            "title": "Fail forward: prerequisites first",
            "blurb": ("Failing a card pulls its shaky prerequisites ahead of "
                     "the retry instead of repeating the card cold."),
            "path": "/status", "anchor": mod.STATUS_ANCHOR})


class StatusTest(unittest.TestCase):
    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.status_section())
        self.assertIn("remediation", mod.status_section())
        self.assertEqual(mod.tour_entry()["anchor"], mod.STATUS_ANCHOR)
        self.assertEqual(mod.tour_entry()["path"], "/status")


class CallerEffectTest(unittest.TestCase):
    """The Due queue pulls a failed concept's prerequisites ahead of it."""

    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("remed mod")
        dbmod.init_db(self.db)
        cards = self.server.tool_list_due_reviews({"limit": 20})["due"]
        ones = [c for c in cards if str(c.get("exercise_type")) == "1"]
        self.card_id = (ones or cards)[0]["id"]
        con = sqlite3.connect(self.db)
        try:
            row = con.execute(
                "SELECT concept_id FROM cards WHERE id=?",
                (self.card_id,)).fetchone()
            self.concept_id = row[0]
            mid = self.out["module_id"]
            con.execute(
                "INSERT INTO concepts(id, module_id, name) VALUES(?,?,?)",
                (mid + ":pre", mid, "Pre Concept"))
            con.execute(
                "INSERT INTO cards(id, concept_id, exercise_type, front, back)"
                " VALUES(?,?,?,?,?)",
                (mid + ":pre:ex001", mid + ":pre", "1", "pre q", "pre a"))
            lessons = json.loads(con.execute(
                "SELECT lessons FROM modules WHERE id=?", (mid,)).fetchone()[0]
                or "[]")
            lessons.append({"concept_id": self.concept_id,
                            "needs": ["Pre Concept"]})
            con.execute("UPDATE modules SET lessons=? WHERE id=?",
                        (json.dumps(lessons), mid))
            con.commit()
        finally:
            con.close()
        self.pre_id = mid + ":pre:ex001"

    def test_failed_concept_pulls_prereq_ahead(self):
        self.server.submit_review(self.card_id, "0", 3)
        due = self.server.tool_list_due_reviews({"limit": 20})["due"]
        ids = [c["id"] for c in due]
        self.assertIn(self.pre_id, ids)
        pre = due[ids.index(self.pre_id)]
        # Ahead of every other due card: the retry is scaffolded.
        self.assertEqual(ids.index(self.pre_id), 0)
        self.assertTrue(pre.get("remedial"))
        self.assertEqual(pre.get("remediation_for"), self.concept_id)

    def test_calm_queue_keeps_legacy_order(self):
        self.server.submit_review(self.card_id, "5", 4)
        due = self.server.tool_list_due_reviews({"limit": 20})["due"]
        self.assertFalse(any(c.get("remedial") for c in due))


if __name__ == "__main__":
    unittest.main()
