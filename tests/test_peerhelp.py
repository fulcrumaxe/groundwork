"""Peer level hints (I-124)."""
import unittest

from groundwork import lessons as lesmod
from groundwork import peerhelp as phmod


def _lesson():
    return {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1,
            "summary": "add() totals two numbers via its defaults.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["Read the defaults."],
            "worked": None}


class NormalizeTest(unittest.TestCase):
    def test_opt_in_only(self):
        self.assertEqual(phmod.normalize_vote((3, True)), (3, True))
        self.assertEqual(phmod.normalize_vote({"level": 2, "opted": True}),
                         (2, True))
        for bad in ((3, False), (5, True), (0, True), ("x", True),
                    None, 42, (None, True)):
            self.assertIsNone(phmod.normalize_vote(bad))


class AggregateTest(unittest.TestCase):
    def test_winner_needs_quorum_and_plurality(self):
        self.assertIsNone(phmod.aggregate([]))
        self.assertIsNone(phmod.aggregate([(3, True)] * 2))  # sub-quorum
        self.assertIsNone(phmod.aggregate([(3, True)] * 2 + [(2, True)] * 2))
        got = phmod.aggregate([(3, True)] * 4 + [(2, True)])
        self.assertEqual(got, {"winner": 3, "votes": 4, "total": 5})

    def test_non_opt_in_never_counts(self):
        self.assertIsNone(phmod.aggregate([(3, False)] * 9))
        self.assertIsNone(phmod.aggregate(None))


class LineHtmlTest(unittest.TestCase):
    def test_silent_until_winner(self):
        self.assertEqual(phmod.line_html([]), "")
        self.assertEqual(phmod.line_html([(1, True), (2, True)]), "")

    def test_verdict_names_level(self):
        out = phmod.line_html([(3, True)] * 3)
        self.assertIn("peerhelp", out)
        self.assertIn("Intermediate", out)
        self.assertIn("3 of 3", out)


class LegacyTest(unittest.TestCase):
    def test_render_levels_byte_identical_without_votes(self):
        base = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertNotIn("peerhelp", base)
        again = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/",
                                     peer_votes=[(1, True)])
        self.assertEqual(again, base)

    def test_winner_appends_hint(self):
        out = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/",
                                   peer_votes=[(4, True)] * 3)
        self.assertIn("Peers found Expert most helpful", out)


class SectionTest(unittest.TestCase):
    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{phmod.STATUS_ANCHOR}'",
                      phmod.section_html())
        e = phmod.tour_entry()
        self.assertEqual(e["id"], "peer-level-hint")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["anchor"], phmod.STATUS_ANCHOR)


if __name__ == "__main__":
    unittest.main()
