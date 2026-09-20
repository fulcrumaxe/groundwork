"""Grading disclosures: every type states its contract (I-181)."""
import unittest

from groundwork import exercises as exmod
from groundwork import grading as gradingmod

from test_web import handler_for, make_module


class DisclosureCoverageTest(unittest.TestCase):
    def test_every_type_has_its_own_contract(self):
        for t in exmod.TYPES:
            with self.subTest(type=t):
                text = gradingmod.disclosure(t)
                self.assertTrue(text)
                self.assertNotEqual(text, "Graded like its exercise family.")

    def test_unknown_type_falls_back(self):
        self.assertEqual(gradingmod.disclosure(999),
                         "Graded like its exercise family.")
        self.assertEqual(gradingmod.disclosure("nope"),
                         "Graded like its exercise family.")

    def test_contracts_match_grader_families(self):
        self.assertIn("0–5", gradingmod.disclosure(1))
        self.assertIn("sandbox", gradingmod.disclosure(12))
        self.assertIn("half", gradingmod.disclosure(5))
        self.assertIn("half", gradingmod.disclosure(21))
        self.assertIn("line", gradingmod.disclosure(13))

    def test_due_shows_disclosure(self):
        tmp, db, server, out = make_module("grading mod")
        h = handler_for(db)
        body = h.due_html()
        self.assertIn("id='grading'", body)
        self.assertIn("How grading works", body)


if __name__ == "__main__":
    unittest.main()
