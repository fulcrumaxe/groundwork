"""Responsive breakpoints audit (I-90): breakpoints under a lens."""
import unittest

from groundwork import responsive as rmod


class ResponsiveTest(unittest.TestCase):
    def test_breakpoints_pinned(self):
        self.assertEqual(rmod.BREAKPOINTS, (360, 768, 1024, 1440))

    def test_boundaries_extraction(self):
        css = ("@media(max-width:640px){a:b}"
               "@media (min-width: 1024px){c:d}"
               "@media(prefers-reduced-motion:reduce){e:f}")
        self.assertEqual(rmod.media_boundaries(css), [640, 1024])
        self.assertEqual(rmod.media_boundaries(""), [])
        self.assertEqual(rmod.media_boundaries(None), [])

    def test_coverage_logic(self):
        css = "@media(max-width:640px){a:b}"
        cov = rmod.coverage(css)
        # max-width:640 reaches 360 but not 768+.
        self.assertTrue(cov[360])
        self.assertFalse(cov[768])
        self.assertFalse(cov[1024])
        self.assertFalse(cov[1440])
        cov2 = rmod.coverage(
            "@media(min-width:900px){a:b}@media(max-width:1500px){c:d}")
        self.assertTrue(all(cov2.values()))
        # No width rules: the audit says zero, honestly.
        self.assertFalse(any(rmod.coverage("").values()))

    def test_offenders_flag_phone_overflow(self):
        html = ("<div style='width:500px'>x</div>"
                "<table width='700'><tr><td>y</td></tr></table>"
                "<p style='width:40px'>z</p>")
        hits = rmod.overflow_offenders(html)
        self.assertIn("fixed-500px", hits)
        self.assertIn("fixed-700px", hits)
        self.assertNotIn("fixed-40px", hits)
        self.assertEqual(rmod.overflow_offenders("<p>fine</p>"), [])
        self.assertEqual(rmod.overflow_offenders(None), [])

    def test_audit_over_shipped_css(self):
        # Wire coverage (narrow_css in the head stylesheet, status
        # section rendering) lands with central wiring and is pinned
        # by tests/test_batch13.py + the chrome sweep.
        from groundwork import web as webmod
        cov = rmod.coverage(webmod.CSS)
        self.assertEqual(set(cov), set(rmod.BREAKPOINTS))

    def test_narrow_css_shape(self):
        css = rmod.narrow_css()
        self.assertIn("@media(max-width:640px)", css.replace(" ", ""))
        self.assertIn("var(--fs-small)", css)
        # The audit's driven fixes: fields capped, labels stack,
        # slider wraps within a shrinkable fieldset, prose breaks.
        nospace = css.replace(" ", "")
        self.assertIn("max-width:100%", nospace)
        self.assertIn("formlabel{display:block", nospace)
        self.assertIn("flex-wrap:wrap", nospace)
        self.assertIn("min-inline-size:0", nospace)
        self.assertIn("overflow-wrap:anywhere", nospace)
        self.assertNotIn("<style", css.lower())
        # The only display rewrite is form labels stacking on phones.
        self.assertNotIn("position", css)
        self.assertEqual(nospace.count("display:"), 1)

    def test_section_html_live_table(self):
        html = rmod.section_html()
        self.assertIn("id='status-b13-responsive'", html)
        for bp in rmod.BREAKPOINTS:
            self.assertIn(f"{bp}px", html)

    def test_tour_entry_shape(self):
        e = rmod.tour_entry()
        self.assertEqual(e, {
            "id": "responsive-audit",
            "kind": "improvement",
            "title": "Responsive audit",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b13-responsive",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "responsive.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
