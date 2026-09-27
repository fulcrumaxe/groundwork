"""Clickable blast-radius dependency graph (I-174)."""
import json
import unittest

from groundwork import blastgraph as bgmod
from groundwork import cards as cardsmod
from groundwork import exercises as exmod


def _card(**kw):
    base = {"id": "c1", "exercise_type": "16", "concept": "parse",
            "payload": json.dumps({"choices": ["load", "main", "cli"],
                                   "answer": "load", "hints": []})}
    base.update(kw)
    return base


class UsableChoicesTest(unittest.TestCase):
    def test_needs_two_to_six_strings(self):
        self.assertEqual(bgmod.usable_choices({}), [])
        self.assertEqual(bgmod.usable_choices({"choices": []}), [])
        self.assertEqual(bgmod.usable_choices({"choices": ["only"]}), [])
        self.assertEqual(bgmod.usable_choices({"choices": ["a"] * 7}), [])
        self.assertEqual(bgmod.usable_choices({"choices": ["a", 3]}), [])
        self.assertEqual(bgmod.usable_choices({"choices": "load"}), [])
        self.assertEqual(bgmod.usable_choices(None), [])
        self.assertEqual(bgmod.usable_choices({"choices": ["a", "b"]}),
                         ["a", "b"])

    def test_rejects_garbage(self):
        self.assertEqual(bgmod.graph_html("c", "nope"), "")
        self.assertEqual(bgmod.graph_html("c", []), "")
        self.assertEqual(bgmod.graph_html("c", ["solo"]), "")
        self.assertEqual(bgmod.edges_svg("c", None), "")
        self.assertFalse(bgmod.has_graph({}))
        self.assertFalse(bgmod.has_graph(None))
        self.assertEqual(bgmod.concept_of({}), "self")
        self.assertEqual(bgmod.concept_of(None), "self")

    def test_legacy_row_matches_cards_branch(self):
        self.assertEqual(
            bgmod.legacy_html(["a", "b"]),
            "<button name='answer' value='a'>a</button> "
            "<button name='answer' value='b'>b</button>")
        self.assertEqual(bgmod.legacy_html([]), "")
        self.assertEqual(bgmod.legacy_html(None), "")


class GraphHtmlTest(unittest.TestCase):
    def test_nodes_post_exact_choice_values(self):
        out = bgmod.graph_html("parse", ["load", "main", "cli"], "c9")
        self.assertIn("<svg class='blastgraph'", out)
        self.assertIn("parse", out)
        for c in ("load", "main", "cli"):
            self.assertIn(f"name='answer' value='{c}'", out)
        self.assertEqual(out.count("class='bg-node'"), 3)
        self.assertIn("marker-end", out)
        self.assertIn("bg-arrow-c9", out)

    def test_marker_ids_unique_per_card(self):
        a = bgmod.graph_html("p", ["x", "y"], "c1")
        b = bgmod.graph_html("p", ["x", "y"], "c2")
        self.assertIn("bg-arrow-c1", a)
        self.assertIn("bg-arrow-c2", b)
        self.assertNotIn("bg-arrow-c2", a)

    def test_escapes_hostile_labels(self):
        out = bgmod.graph_html("<b>", ["<script>", "ok"], "c1")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;", out)

    def test_ascii_only(self):
        bgmod.graph_html("parse", ["load", "main", "cli"], "c1").encode("ascii")
        bgmod.edges_svg("parse", ["load", "main"], "c1").encode("ascii")
        bgmod.section_html().encode("ascii")

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{bgmod.STATUS_ANCHOR}'", bgmod.section_html())
        self.assertEqual(bgmod.tour_entry(), {
            "id": "blastgraph-clickable",
            "kind": "improvement",
            "title": "Clickable blast-radius graph",
            "blurb": "Blast-radius choices answer as nodes on a small graph.",
            "path": "/status",
            "anchor": "status-b26-blastgraph",
        })


class CallerEffectTest(unittest.TestCase):
    def test_answer_widget_graph_with_legacy_fallback_pinned(self):
        widget = cardsmod.answer_widget(_card(), 0, "/due")
        self.assertIn("<svg class='blastgraph'", widget)
        for c in ("load", "main", "cli"):
            self.assertIn(f"name='answer' value='{c}'", widget)
        ex = {"type": 16, "payload": {"choices": ["load", "main", "cli"],
                                      "answer": "load"}}
        self.assertTrue(exmod.grade(ex, "load")["pass"])
        self.assertFalse(exmod.grade(ex, "main")["pass"])
        bare = _card(payload=json.dumps({"hints": []}))
        self.assertEqual(bgmod.branch_html(bare, {}, "c1"),
                         " " + cardsmod._confidence())
        one = _card(payload=json.dumps({"choices": ["solo"], "hints": []}))
        self.assertEqual(
            bgmod.branch_html(one, {"choices": ["solo"]}, "c1"),
            "<button name='answer' value='solo'>solo</button> "
            + cardsmod._confidence())


if __name__ == "__main__":
    unittest.main()
