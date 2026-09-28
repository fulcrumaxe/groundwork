"""One submit per card per 5s: double-click guard (I-199)."""
import json
import re
import unittest

from groundwork import cards as cardsmod
from groundwork import spamguard as sgmod
from groundwork import web as webmod


def _card(**kw):
    base = {"id": "c1", "exercise_type": "8", "concept": "predict",
            "payload": json.dumps({"hints": []})}
    base.update(kw)
    return base


def _sel_literal(js):
    m = re.search(r"var SEL=\"((?:[^\"\\]|\\.)*)\"", js)
    assert m, "guard_js must embed its selector as var SEL=\"...\""
    return m.group(1).encode().decode("unicode_escape")


class SpamguardTest(unittest.TestCase):
    def test_js_targets_real_review_forms(self):
        js = sgmod.guard_js()
        sel = _sel_literal(js)
        # Both forms cards.answer_widget emits (answer + give-up).
        self.assertIn("form[action^='/cards/'][action$='/review']", sel)
        self.assertIn("submit", js)

    def test_effect_second_submit_within_5s_cancelled(self):
        # Behavioral effect: per-card timestamp throttle.
        js = sgmod.guard_js()
        self.assertIn("Date.now()", js)
        self.assertIn("5000", js)
        self.assertIn("preventDefault", js)
        # Keyed per card, not per form: the card id parsed from the
        # action URL, shared by the answer + give-up forms.
        self.assertIn("/cards/", js)
        self.assertIn("last[k]", js)
        # First submit stamps and proceeds: the stamp follows the block.
        self.assertLess(js.index("preventDefault"), js.index("last[k]=now"))
        # Blocked repeats get a status note, not a silent drop.
        self.assertIn("gw-throttle", js)
        self.assertIn("role", js)
        self.assertIn("Already submitted", js)
        # Coexistence: never silences sibling submit listeners,
        # never touches fetch or storage.
        self.assertNotIn("stopPropagation", js)
        self.assertNotIn("stopImmediatePropagation", js)
        self.assertNotIn("fetch(", js)
        self.assertNotIn("localStorage", js)
        self.assertNotIn("sessionStorage", js)

    def test_fallback_legacy_plain_submit_pinned(self):
        # Without JS/DOM the forms submit normally: feature-detect
        # early return, and the server HTML carries no JS dependency.
        js = sgmod.guard_js()
        self.assertIn("if(!document.querySelectorAll", js)
        widget = cardsmod.answer_widget(_card(), 0, "/due")
        self.assertIn("/cards/c1/review", widget)
        self.assertNotIn("onsubmit", widget.lower())
        self.assertNotIn("data-spamguard", widget)
        self.assertNotIn("gw-throttle", widget)

    def test_page_wire_carries_guard(self):
        # Caller proof: every page ships the throttle script + note CSS.
        body = webmod.page("T", "<p>b</p>").decode("utf-8")
        self.assertIn(sgmod.SCRIPT_MARKER, body)
        self.assertIn(".gw-throttle", body)
        self.assertIn("last[k]=now", body)

    def test_window_clamp_fail_closed(self):
        self.assertEqual(sgmod.window_ms(), sgmod.WINDOW_MS)
        self.assertEqual(sgmod.window_ms(2000), 2000)
        for bad in (None, "fast", 0, 999, 30001, -5, object()):
            self.assertEqual(sgmod.window_ms(bad), sgmod.WINDOW_MS)
        self.assertIn("2000", sgmod.guard_js(window=2000))
        self.assertIn("5000", sgmod.guard_js(window="fast"))

    def test_js_selector_quotes_bracket_scoped(self):
        sel = _sel_literal(sgmod.guard_js())
        self.assertEqual(sel.count("["), sel.count("]"))
        neb = re.sub(r"\[[^\[\]]*\]", "", sel)
        self.assertNotIn("'", neb)
        self.assertNotIn('"', neb)

    def test_custom_selector_validation_fail_closed(self):
        good = sgmod.form_selector("form[data-queue='due']")
        self.assertTrue(good.startswith("form[data-queue='due']"))
        for bad in (None, 42, "", "form'evil",
                    "form[data-x='a'", "form<>",
                    "form[data-x='a']`", "  "):
            self.assertEqual(sgmod.form_selector(bad),
                             sgmod.FORM_SELECTOR)
        js = sgmod.guard_js("form'evil")
        self.assertIn(sgmod.FORM_SELECTOR.replace("'", "\x27")[:12], js)

    def test_css_static_no_style_tags_no_motion(self):
        css = sgmod.guard_css()
        self.assertIn("gw-throttle", css)
        # Static note: nothing animates, reduced-motion safe by build.
        self.assertNotIn("animation", css)
        self.assertNotIn("@keyframes", css)
        low = css.lower()
        self.assertNotIn("<style", low)
        self.assertNotIn("</style", low)

    def test_helpers_fail_closed_never_raise(self):
        self.assertEqual(sgmod.form_selector(None), sgmod.FORM_SELECTOR)
        for fn in (sgmod.guard_js, sgmod.guard_css,
                   sgmod.section_html, sgmod.demo_html):
            self.assertTrue(fn())
        self.assertTrue(sgmod.guard_js(None))
        self.assertTrue(sgmod.guard_js(42))
        self.assertTrue(sgmod.guard_js(window=object()))

    def test_section_html_anchor(self):
        html = sgmod.section_html()
        self.assertIn("id='status-b29-spamguard'", html)
        self.assertIn("guard_js", html)
        self.assertIn("guard_css", html)

    def test_tour_entry_shape(self):
        e = sgmod.tour_entry()
        self.assertEqual(e, {
            "id": "double-submit-guard",
            "kind": "improvement",
            "title": "Double-submit guard",
            "blurb": e["blurb"],
            "path": "/status",
            "anchor": "status-b29-spamguard",
        })
        self.assertTrue(e["blurb"])
        self.assertTrue(e["path"].startswith("/"))

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "spamguard.py").read_text(encoding="utf-8")
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
