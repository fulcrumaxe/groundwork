"""Inline SVG call graphs (I-126)."""
import json
import unittest

from groundwork import callgraph as cgmod
from groundwork import db as dbmod

from test_web import handler_for, make_module


class GraphSvgTest(unittest.TestCase):
    def test_legacy_no_data_renders_nothing(self):
        self.assertEqual(cgmod.graph_svg({}), "")
        self.assertEqual(cgmod.graph_svg(None), "")
        self.assertEqual(cgmod.graph_svg({"name": "f"}), "")
        self.assertEqual(cgmod.block_html({}), "")
        self.assertFalse(cgmod.has_graph({"name": "f"}))

    def test_rejects_garbage(self):
        self.assertEqual(cgmod.graph_svg(42), "")
        self.assertEqual(cgmod.block_html(["x"]), "")
        self.assertEqual(cgmod.callers_of(None), [])
        self.assertEqual(cgmod.callees_of("s"), [])

    def test_callers_left_callees_right_with_arrows(self):
        svg = cgmod.graph_svg({"name": "f", "callers": ["a", "b"],
                               "callees": ["c"]})
        self.assertIn("<svg", svg)
        self.assertIn("cg-caller", svg)
        self.assertIn("cg-callee", svg)
        self.assertIn("cg-self", svg)
        self.assertIn("marker-end", svg)
        # Column order lives in x positions, not DOM order (the <title>
        # names the self node before any box is emitted): callers left,
        # self center, callees right.
        self.assertIn("<g class='cg-caller'><rect x='8'", svg)
        self.assertIn("<g class='cg-self'><rect x='128'", svg)
        self.assertIn("<g class='cg-callee'><rect x='248'", svg)

    def test_escapes_hostile_labels(self):
        svg = cgmod.graph_svg({"name": "<b>", "callers": ["<script>"],
                               "callees": []})
        self.assertNotIn("<script>", svg)
        self.assertIn("&lt;script&gt;", svg)

    def test_caps_sides(self):
        lesson = {"name": "f",
                  "callers": [f"c{i}" for i in range(9)], "callees": []}
        self.assertEqual(len(cgmod.callers_of(lesson)), cgmod.MAX_SIDE)

    def test_block_wraps_figure(self):
        out = cgmod.block_html({"name": "f", "callers": ["a"],
                                "callees": ["c"]})
        self.assertIn("<figure", out)
        self.assertIn("<svg", out)


class CallerEffectTest(unittest.TestCase):
    def test_module_html_graph_for_data_lesson(self):
        tmp, db, server, out = make_module("callgraph mod")
        mid = out["module_id"]
        con = dbmod.connect(db)
        try:
            row = con.execute("SELECT lessons FROM modules WHERE id=?",
                              (mid,)).fetchone()[0]
            lessons = json.loads(row or "[]")
            self.assertTrue(lessons)
            lessons[0]["callers"] = ["helper"]
            lessons[0]["callees"] = ["total"]
            con.execute("UPDATE modules SET lessons=? WHERE id=?",
                        (json.dumps(lessons), mid))
            con.commit()
        finally:
            con.close()
        body = handler_for(db).module_html(mid)
        self.assertIn("<svg class='callgraph'", body)

    def test_module_html_byte_identical_without_data(self):
        # Legacy fixture lesson carries no call data: no graph figure.
        # (The module summary itself mentions callgraph, so assert on
        # the emitted artifacts, not the bare word.)
        tmp, db, server, out = make_module("callgraph legacy mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("<svg class='callgraph'", body)
        self.assertNotIn("callgraph-wrap", body)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{cgmod.STATUS_ANCHOR}'",
                      cgmod.section_html())
        e = cgmod.tour_entry()
        self.assertEqual(e, {
            "id": "callgraph-svg",
            "kind": "improvement",
            "title": "Call graphs as inline SVG",
            "blurb": "Caller/callee lists render as a small inline "
                     "SVG graph per lesson.",
            "path": "/status",
            "anchor": "status-b21-callgraph",
        })


if __name__ == "__main__":
    unittest.main()
