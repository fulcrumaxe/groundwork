"""Dual-coding packs (F-60): words + diagram + trace per idea."""
import re
import unittest

from groundwork import dualcode as dcmod


class DualcodeTest(unittest.TestCase):
    def test_pack_has_all_three_channels(self):
        pack = dcmod.pack_html("Backoff", "Wait longer each time.",
                               ["try", "sleep", "retry"], ["err", "1s", "ok"])
        self.assertIn("dual-words", pack)
        self.assertIn("Wait longer each time.", pack)
        self.assertIn("<svg", pack)
        self.assertIn("dual-trace", pack)
        self.assertIn("Backoff", pack)

    def test_diagram_boxes_and_arrows(self):
        svg = dcmod.diagram_svg(["a", "b", "c"])
        self.assertEqual(svg.count("<rect"), 3)
        self.assertEqual(svg.count("<line"), 2)  # n-1 arrows
        self.assertIn("role='img'", svg)
        self.assertIn("var(--paper)", svg)
        self.assertIn("var(--ink)", svg)
        self.assertEqual(dcmod.diagram_svg([]), "")
        self.assertEqual(dcmod.diagram_svg(None), "")

    def test_diagram_caps_and_escapes(self):
        svg = dcmod.diagram_svg([f"step {i}" for i in range(30)])
        self.assertEqual(svg.count("<rect"), dcmod.MAX_STEPS)
        evil = dcmod.diagram_svg(["<script>alert(1)</script>"])
        self.assertNotIn("<script>", evil)

    def test_trace_states_align(self):
        tbl = dcmod.trace_table(["a", "b"], ["only-one"])
        self.assertIn("only-one", tbl)
        self.assertIn("—", tbl)  # missing state renders a dash, not blank
        self.assertEqual(dcmod.trace_table([]), "")

    def test_pack_degrades_gracefully(self):
        bare = dcmod.pack_html("", "", [], None)
        self.assertIn("dual-pack", bare)
        self.assertNotIn("<svg", bare)
        self.assertNotIn("<table", bare)
        for bad in (None, 42, object()):
            self.assertIn("dual-pack", dcmod.pack_html(bad, bad, bad, bad))

    def test_section_html_sample_pack(self):
        html = dcmod.section_html()
        self.assertIn("id='status-b13-dualcode'", html)
        self.assertIn("pack_html", html)
        self.assertIn("<svg", html)

    def test_tour_entry_shape(self):
        e = dcmod.tour_entry()
        self.assertEqual(e, {
            "id": "dual-coding",
            "kind": "feature",
            "title": "Dual-coding packs",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-dualcode",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "dualcode.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
