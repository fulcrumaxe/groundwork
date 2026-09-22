"""Diagrams-per-lesson quality gate (I-125)."""
import unittest

from groundwork import diagrams as dgmod

from test_web import handler_for, make_module


def _text_only():
    return {"concept_id": "c", "name": "add",
            "summary": "Words with no picture."}


def _rich():
    return {"concept_id": "c", "name": "add",
            "summary": "add() totals two numbers.",
            "source": "def add(a, b):\n    return a + b\n",
            "dualcode": {"steps": ["Read the defaults."],
                         "states": ["a=2"]},
            "worked": {"trace": {"steps": ["total=5"]}}}


class DiagramsGateTest(unittest.TestCase):
    def test_legacy_empty_passes(self):
        self.assertTrue(dgmod.gate_lesson({})["ok"])
        self.assertTrue(dgmod.gate_lesson(None)["ok"])
        self.assertEqual(dgmod.badge_html({}), "")
        self.assertEqual(dgmod.toc_mark({}), "")

    def test_text_only_fails(self):
        gate = dgmod.gate_lesson(_text_only())
        self.assertFalse(gate["ok"])
        self.assertEqual(gate["visuals"], 0)
        self.assertEqual(len(gate["missing"]), 4)
        badge = dgmod.badge_html(_text_only())
        self.assertIn("needs-visual", badge)
        self.assertIn("diagram", badge)
        self.assertEqual(dgmod.toc_mark(_text_only()), " · needs visual")

    def test_trace_and_dualcode_pass(self):
        gate = dgmod.gate_lesson(_rich())
        self.assertTrue(gate["ok"])
        self.assertEqual(dgmod.badge_html(_rich()), "")
        self.assertEqual(dgmod.toc_mark(_rich()), "")

    def test_source_counts_as_code(self):
        lesson = {"summary": "x", "source": "def f():\n    pass\n"}
        self.assertTrue(dgmod.gate_lesson(lesson)["ok"])

    def test_gate_module_failing_ids(self):
        got = dgmod.gate_module({"a": _text_only(), "b": _rich()})
        self.assertEqual(got["failing"], ["a"])

    def test_rejects_garbage(self):
        self.assertTrue(dgmod.gate_lesson(42)["ok"])
        self.assertEqual(dgmod.gate_module(None)["failing"], [])


class CallerEffectTest(unittest.TestCase):
    def test_module_html_no_notice_for_passing_fixture(self):
        tmp, db, server, out = make_module("diagrams mod")
        h = handler_for(db)
        body = h.module_html(out["module_id"])
        self.assertNotIn("needs-visual", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{dgmod.STATUS_ANCHOR}'",
                      dgmod.section_html())
        e = dgmod.tour_entry()
        self.assertEqual(e["id"], "diagrams-gate")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], dgmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
