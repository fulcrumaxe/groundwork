"""Sequence diagrams for 3-step call chains (I-127)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import seqdiag as sdmod

from test_web import handler_for, make_module


def _grounded():
    return {"id": "ex1", "type": 10, "concept": "resize",
            "front": "Order the calls through `resize`.",
            "back": "handle_resize → resize → repaint",
            "payload": {"lines": ["repaint", "resize", "handle_resize"],
                        "solution": ["handle_resize", "resize", "repaint"],
                        "grounded": True}}


def _ungrounded():
    return {"id": "ex2", "type": 10, "concept": "solo",
            "front": "Order the calls through `solo`.",
            "back": "solo",
            "payload": {"lines": ["solo"], "solution": ["solo"],
                        "grounded": False}}


def _card(exercise):
    return {"id": exercise["id"], "exercise_type": 10,
            "concept": exercise["concept"],
            "payload": json.dumps(exercise["payload"])}


class ChainExtractTest(unittest.TestCase):
    def test_grounded_chain_extracted(self):
        self.assertEqual(sdmod.chain_of(_grounded()),
                         ["handle_resize", "resize", "repaint"])

    def test_ungrounded_single_kept_for_gate(self):
        self.assertEqual(sdmod.chain_of(_ungrounded()), ["solo"])

    def test_rejects_garbage(self):
        self.assertEqual(sdmod.chain_of(None), [])
        self.assertEqual(sdmod.chain_of(42), [])
        self.assertEqual(sdmod.chain_of({}), [])
        self.assertEqual(sdmod.chain_of({"payload": {"solution": "nope"}}),
                         [])
        self.assertEqual(sdmod.participants(None), [])

    def test_participants_cleaned_and_capped(self):
        got = sdmod.participants([" a ", "", None, "b", "c", "d"])
        self.assertEqual(got, ["a", "b", "c"])


class SequenceSvgTest(unittest.TestCase):
    def test_three_lifelines_in_order(self):
        svg = sdmod.sequence_svg(["handle_resize", "resize", "repaint"])
        self.assertIn("<svg", svg)
        self.assertEqual(svg.count("seq-life"), 3)
        self.assertEqual(svg.count("seq-call"), 2)
        self.assertLess(svg.index("handle_resize"), svg.index("resize"))
        self.assertLess(svg.index("resize"), svg.index("repaint"))

    def test_two_node_chain_draws(self):
        svg = sdmod.sequence_svg(["caller", "concept"])
        self.assertIn("<svg", svg)
        self.assertEqual(svg.count("seq-life"), 2)

    def test_short_chain_renders_nothing(self):
        self.assertEqual(sdmod.sequence_svg(["solo"]), "")
        self.assertEqual(sdmod.sequence_svg([]), "")
        self.assertEqual(sdmod.sequence_svg(None), "")

    def test_labels_escaped(self):
        svg = sdmod.sequence_svg(["<b>a</b>", "c&d"])
        self.assertNotIn("<b>", svg)
        self.assertIn("&amp;", svg)


class FigureTest(unittest.TestCase):
    def test_figure_caption_names_concept(self):
        fig = sdmod.figure_html(_grounded(), "resize")
        self.assertIn("<figure", fig)
        self.assertIn("resize", fig)
        self.assertIn("handle_resize", fig)

    def test_ungrounded_renders_nothing(self):
        self.assertEqual(sdmod.figure_html(_ungrounded(), "solo"), "")
        self.assertEqual(sdmod.figure_html({}, "x"), "")
        self.assertEqual(sdmod.figure_html(None), "")


class CallerEffectTest(unittest.TestCase):
    def test_widget_grows_diagram_for_grounded_type10(self):
        out = cardsmod.answer_widget(_card(_grounded()))
        self.assertIn("<svg class='seq-diagram'", out)
        self.assertIn("seq-figure", out)
        # The prompt still renders below the diagram.
        self.assertIn("Check order", out)

    def test_widget_legacy_fallbacks_have_no_diagram(self):
        out = cardsmod.answer_widget(_card(_ungrounded()))
        self.assertNotIn("seq-diagram", out)
        bare = dict(_card(_grounded()))
        bare["payload"] = json.dumps({"lines": ["a", "b"]})
        self.assertNotIn("seq-diagram", cardsmod.answer_widget(bare))

    def test_module_html_no_diagram_without_type10(self):
        tmp, db, server, out = make_module("seqdiag mod")
        h = handler_for(db)
        body = h.module_html(out["module_id"])
        self.assertNotIn("seq-diagram", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{sdmod.STATUS_ANCHOR}'",
                      sdmod.section_html())
        e = sdmod.tour_entry()
        self.assertEqual(e, {
            "id": "seqdiag-chains",
            "kind": "improvement",
            "title": "Call chains drawn as sequence diagrams",
            "blurb": "Order-the-calls chains draw as lifelines and "
                     "arrows on the lesson page.",
            "path": "/status",
            "anchor": "status-b21-seqdiag",
        })


if __name__ == "__main__":
    unittest.main()
