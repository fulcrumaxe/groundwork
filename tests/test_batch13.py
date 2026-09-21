"""Batch 13 wiring: every item registered, styled, toured, and served.

Pins the central-wiring commit: 17 new AREAS entries, the five head
wires, favicon/OG/density head+foot wires, the 500 wrapper, the
review-note line, 16 tour entries, and the status home. Per-module
behavior stays in the focused test files; this file only proves the
wires meet.
"""
import unittest
from http.server import BaseHTTPRequestHandler

from groundwork import batch13 as b13mod
from groundwork import formerr as formerrmod
from groundwork import modularity as modularitymod
from groundwork import tour as tourmod
from groundwork import web as webmod

AREAS13 = ["errpage", "formerr", "selection", "scrollbar", "pageicon",
           "ogtags", "density", "responsive", "dualcode", "interleave",
           "spacingopt", "retrieval", "predict", "confweight",
           "calibdrill", "overconf", "batch13"]

ANCHORS13 = ["status-b13-errpage", "status-b13-formerr",
             "status-b13-selection", "status-b13-scrollbar",
             "status-b13-pageicon", "status-b13-ogtags",
             "status-b13-density", "status-b13-responsive",
             "status-b13-dualcode", "status-b13-interleave",
             "status-b13-spacingopt", "status-b13-retrieval",
             "status-b13-predict", "status-b13-confweight",
             "status-b13-calibdrill", "status-b13-overconf"]


class Batch13WiringTest(unittest.TestCase):
    def test_areas_registered(self):
        for area in AREAS13:
            self.assertIn(area, modularitymod.AREAS)
        self.assertEqual(modularitymod.check(), [])

    def test_head_css_wires(self):
        css = webmod.CSS
        for token in ("::selection", "scrollbar-width:thin",
                      ".field-error", "data-density",
                      "@media(max-width:640px)"):
            self.assertIn(token, css, token)

    def test_head_meta_wires(self):
        raw = webmod.page("Demo title", "<p>x</p>",
                          counts={"due": 3, "modules": 1, "history": 0},
                          lede="Study closures first.").decode()
        self.assertIn("id='gw-icon'", raw)
        self.assertIn("rel='icon'", raw)
        self.assertIn("data:image/svg+xml,", raw)
        self.assertIn("og:title", raw)
        self.assertIn("Demo title", raw)
        self.assertIn("Study closures first.", raw)
        self.assertNotIn("og:url", raw)
        # Head carries the density toggle + foot carries its script.
        self.assertIn("id='gw-density-toggle'", raw)
        self.assertIn("data-density-toggle", raw)

    def test_status_home_renders_all_anchors(self):
        home = b13mod.batch13_html()
        for anchor in ANCHORS13:
            self.assertIn(f"id='{anchor}'", home, anchor)
        self.assertIn("status-batch13", home)

    def test_tour_entries_match_modules(self):
        ids = ["error-pages", "inline-errors", "selection-accent",
               "palette-scrollbars", "due-favicon", "share-unfurls",
               "density-toggle", "responsive-audit", "dual-coding",
               "interleaving", "spacing-optimizer", "retrieval-first",
               "predict-reveal", "conf-scoring", "calib-drills",
               "overconf-cards"]
        for eid in ids:
            with self.subTest(entry=eid):
                e = tourmod.BY_ID[eid]
                self.assertTrue(e["anchor"].startswith("status-b13-"))
                self.assertIn(f"id='{e['anchor']}'", b13mod.batch13_html())

    def test_500_wrapper_renders_chrome_page(self):
        h = webmod.Handler.__new__(webmod.Handler)
        sent = {}
        h._send = lambda data, code=200, ctype="text/html": sent.update(
            data=data, code=code)
        h._nav_counts = lambda: {"due": 1, "modules": 0, "history": 0}
        orig = BaseHTTPRequestHandler.handle_one_request
        BaseHTTPRequestHandler.handle_one_request = (
            lambda self: (_ for _ in ()).throw(ValueError("boom")))
        try:
            webmod.Handler.handle_one_request(h)
        finally:
            BaseHTTPRequestHandler.handle_one_request = orig
        self.assertEqual(sent["code"], 500)
        body = sent["data"].decode()
        self.assertIn("id='server-error'", body)
        self.assertIn("id='sitenav'", body)
        self.assertIn("ValueError", body)
        self.assertNotIn("Traceback", body)

    def test_500_wrapper_lets_disconnects_through(self):
        h = webmod.Handler.__new__(webmod.Handler)
        orig = BaseHTTPRequestHandler.handle_one_request
        BaseHTTPRequestHandler.handle_one_request = (
            lambda self: (_ for _ in ()).throw(BrokenPipeError()))
        try:
            with self.assertRaises(BrokenPipeError):
                webmod.Handler.handle_one_request(h)
        finally:
            BaseHTTPRequestHandler.handle_one_request = orig

    def test_shipped_css_parses_clean(self):
        # Regression (Batch 13): an unclosed skeletons @media plus an
        # unclosed density string silently swallowed every later rule
        # (unit tests asserting text inclusion stayed green; only the
        # rendered cascade noticed). The shipped stylesheet must close
        # every block it opens and every string it starts.
        css = webmod.CSS
        depth = 0
        for ch in css:
            if ch == "{":
                depth += 1
            elif ch == "}":
                depth = max(0, depth - 1)
        self.assertEqual(depth, 0)
        self.assertEqual(css.count("'") % 2, 0)

    def test_review_note_wired(self):
        import inspect
        src = inspect.getsource(webmod.Handler.do_POST)
        self.assertIn("formerrmod.review_note(raw)", src)
        self.assertIn("cerr + scrollposmod.restore_js", src)
        self.assertTrue(formerrmod.review_note("confidence=9"))


if __name__ == "__main__":
    unittest.main()
