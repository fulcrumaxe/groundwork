"""Optimistic UI on review submit (I-82): disable + spinner."""
import re
import unittest

from groundwork import optimistic as optmod


def _sel_literal(js):
    m = re.search(r"var SEL=\"((?:[^\"\\]|\\.)*)\"", js)
    assert m, "optimistic_js must embed its selector as var SEL=\"...\""
    return m.group(1).encode().decode("unicode_escape")


class OptimisticTest(unittest.TestCase):
    def test_js_targets_real_review_forms(self):
        js = optmod.optimistic_js()
        sel = _sel_literal(js)
        # Both forms cards.answer_widget emits (answer + give-up).
        self.assertIn("form[action^='/cards/'][action$='/review']", sel)
        self.assertIn("submit", js)

    def test_js_disables_and_spins_without_hijacking_submit(self):
        js = optmod.optimistic_js()
        self.assertIn("disabled", js)
        self.assertIn("gw-spinner", js)
        self.assertIn("Working", js)
        self.assertIn("addEventListener", js)
        # Presentation-only guard: grading, collapse-fetch, and
        # draft-clear listeners must still run.
        self.assertNotIn("preventDefault", js)
        self.assertNotIn("stopPropagation", js)
        self.assertNotIn("fetch(", js)
        self.assertNotIn("localStorage", js)
        self.assertNotIn("sessionStorage", js)

    def test_spinner_cycle_under_300ms(self):
        css = optmod.optimistic_css()
        durations = [int(m.group(1))
                     for m in re.finditer(r"(\d+)\s*ms", css)]
        self.assertTrue(durations)
        for ms in durations:
            self.assertLessEqual(ms, 300)
        self.assertIn("animation", css)
        self.assertIn("@keyframes", css)

    def test_reduced_motion_static_fallback(self):
        css = optmod.optimistic_css().replace(" ", "")
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("animation:none", css)
        # The static fallback text the guard inserts for all users,
        # and the only thing that moves under reduced motion.
        self.assertIn("Working", optmod.optimistic_js())

    def test_raw_declarations_only_no_style_tags(self):
        css = optmod.optimistic_css().lower()
        self.assertNotIn("<style", css)
        self.assertNotIn("</style", css)
        self.assertNotIn("<style", optmod.optimistic_js().lower()
                         .replace("<script", ""))

    def test_js_selector_quotes_bracket_scoped(self):
        # Same rule as autofocus.field_selector: quotes live only
        # inside [...] attribute brackets.
        sel = _sel_literal(optmod.optimistic_js())
        self.assertEqual(sel.count("["), sel.count("]"))
        neb = re.sub(r"\[[^\[\]]*\]", "", sel)
        self.assertNotIn("'", neb)
        self.assertNotIn('"', neb)

    def test_custom_selector_validation_fail_closed(self):
        good = optmod.form_selector("form[data-queue='due']")
        self.assertTrue(good.startswith("form[data-queue='due']"))
        for bad in (None, 42, "", "form'evil",
                    "form[data-x='a'", "form<>",
                    "form[data-x='a']`", "  "):
            self.assertEqual(optmod.form_selector(bad),
                             optmod.FORM_SELECTOR)
        # A bad custom selector never breaks the snippet.
        js = optmod.optimistic_js("form'evil")
        self.assertIn(optmod.FORM_SELECTOR.replace("'", "\x27")[:12], js)

    def test_helpers_fail_closed_never_raise(self):
        for bad in (None, "fast", -50, 9999, object()):
            ms = optmod.spin_ms(bad)
            self.assertGreaterEqual(ms, 0)
            self.assertLessEqual(ms, 300)
        self.assertEqual(optmod.spin_ms(), optmod.SPIN_MS)
        self.assertEqual(optmod.form_selector(None), optmod.FORM_SELECTOR)
        for fn in (optmod.optimistic_js, optmod.optimistic_css,
                   optmod.section_html, optmod.demo_html):
            self.assertTrue(fn())
        self.assertTrue(optmod.optimistic_js(None))
        self.assertTrue(optmod.optimistic_js(42))

    def test_section_html_anchor(self):
        html = optmod.section_html()
        self.assertIn("id='status-b12-optimistic'", html)
        self.assertIn("optimistic_js", html)
        self.assertIn("optimistic_css", html)

    def test_tour_entry_shape(self):
        e = optmod.tour_entry()
        self.assertEqual(e, {
            "id": "optimistic-submit",
            "kind": "improvement",
            "title": "Optimistic submit",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b12-optimistic",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        # Scans the module only: this test's own source necessarily
        # names the markers it guards against.
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "optimistic.py").read_text(encoding="utf-8")
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
