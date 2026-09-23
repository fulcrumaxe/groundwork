"""Skill-atom decomposition (F-99): failing concepts split into sub-skills."""
import unittest

from groundwork import db as dbmod
from groundwork import skillatoms as mod

from test_web import make_module


class ClassifyTest(unittest.TestCase):
    def test_recall_keyword(self):
        self.assertEqual(mod.classify_miss("I forgot the definition"), "recall")

    def test_discriminate_keyword(self):
        self.assertEqual(
            mod.classify_miss("confused it with the lookalike"), "discriminate")

    def test_unknown_defaults_procedure(self):
        self.assertEqual(mod.classify_miss("it just broke"), "procedure")
        self.assertEqual(mod.classify_miss(""), "procedure")
        self.assertEqual(mod.classify_miss(None), "procedure")


class DecomposeTest(unittest.TestCase):
    def test_splits_into_ranked_atoms(self):
        attempts = [
            {"ok": False, "error": "forgot the definition"},
            {"ok": False, "error": "confused it with the lookalike, mistook X for Y"},
            {"ok": False, "error": "mistook it for the other one"},
            {"ok": True, "error": ""},
        ]
        atoms = mod.decompose("retest windows", attempts)
        kinds = [a["atom"].split("::")[-1] for a in atoms]
        self.assertIn("discriminate", kinds)
        self.assertIn("recall", kinds)
        self.assertLessEqual(len(atoms), 4)

    def test_atoms_come_out_in_canonical_order(self):
        attempts = [
            {"ok": False, "error": "use it in a new case"},
            {"ok": False, "error": "forgot the definition"},
        ]
        kinds = [a["atom"].split("::")[-1]
                 for a in mod.decompose("c", attempts)]
        self.assertEqual(kinds, ["recall", "transfer"])

    def test_no_data_falls_back_to_single_atom(self):
        atoms = mod.decompose("retest windows", [])
        self.assertEqual(len(atoms), 1)
        self.assertTrue(atoms[0]["atom"].endswith("::all"))

    def test_bad_input_never_raises(self):
        self.assertEqual(len(mod.decompose("", None)), 1)
        self.assertEqual(len(mod.decompose("c", "nope")), 1)


class NeedsSplitTest(unittest.TestCase):
    def test_requires_trailing_run(self):
        self.assertFalse(mod.needs_split([{"ok": False}, {"ok": True}]))
        self.assertTrue(mod.needs_split([{"ok": False}, {"ok": False}]))

    def test_empty_is_legacy_calm(self):
        for bad in (None, [], "x"):
            self.assertFalse(mod.needs_split(bad))


class HtmlTest(unittest.TestCase):
    def test_empty_renders_empty(self):
        self.assertEqual(mod.section_html("c", []), "")
        self.assertEqual(mod.section_html("c", None), "")

    def test_atoms_render_section(self):
        body = mod.section_html("sched", mod.decompose("sched", []))
        self.assertIn("skill-atoms", body)
        self.assertIn("sched", body)


class CallerEffectTest(unittest.TestCase):
    """Grading splits the concept: two trailing fails earn atoms."""

    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("atoms mod")
        dbmod.init_db(self.db)
        cards = self.server.tool_list_due_reviews({"limit": 20})["due"]
        ones = [c for c in cards if str(c.get("exercise_type")) == "1"]
        self.card_id = (ones or cards)[0]["id"]

    def test_two_trailing_fails_earn_atoms(self):
        out = self.server.submit_review(self.card_id, "0", 3)
        self.assertEqual(out.get("atoms", ""), "")
        out = self.server.submit_review(self.card_id, "0", 3)
        self.assertIn("skill-atoms", out.get("atoms", ""))

    def test_passing_reviews_render_no_atoms(self):
        out = self.server.submit_review(self.card_id, "5", 4)
        self.assertEqual(out.get("atoms", ""), "")


if __name__ == "__main__":
    unittest.main()
