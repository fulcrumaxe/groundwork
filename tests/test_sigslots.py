"""Signature skeleton with per-param slots and ticks (I-179)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import emoji as emojimod
from groundwork import exercises as exmod
from groundwork import sigslots as mod

SIG = "fetch(url, timeout, retries)"


def _card(etype=3, signature=SIG, choices="default"):
    if choices == "default":
        choices = [SIG, "fetch(url)", "fetch(retries, timeout, url)"]
    payload = {"func": "fetch", "signature": signature,
               "answer": signature, "choices": choices}
    return {"id": "s1", "exercise_type": etype,
            "payload": json.dumps(payload)}


class SigslotsParseTest(unittest.TestCase):
    def test_def_line_with_defaults_annotations_stars(self):
        self.assertEqual(
            mod.params_of(
                "def fetch(url, timeout=30, *args, retries: int = 3, **kw):"),
            ["url", "timeout", "args", "retries", "kw"])

    def test_bare_call(self):
        self.assertEqual(mod.params_of(SIG), ["url", "timeout", "retries"])

    def test_nested_default_commas_do_not_split(self):
        self.assertEqual(mod.params_of("f(a=(1, 2), b='x,y')"), ["a", "b"])

    def test_markers_and_empty_are_skipped(self):
        self.assertEqual(mod.params_of("f(a, /, *, b)"), ["a", "b"])
        self.assertEqual(mod.params_of("f()"), [])
        self.assertEqual(mod.params_of("fetch(...)"), [])

    def test_hostile_is_empty(self):
        for bad in (None, 5, ["x"], "", "no parens here"):
            self.assertEqual(mod.params_of(bad), [])

    def test_func_of(self):
        self.assertEqual(mod.func_of("def m.fetch(url):"), "fetch")
        self.assertEqual(mod.func_of(SIG), "fetch")
        self.assertEqual(mod.func_of(None), "")
        self.assertEqual(mod.func_of("((( nope"), "")


class SigslotsTicksTest(unittest.TestCase):
    def test_partial_typing_ticks_only_finished_words(self):
        self.assertEqual(
            mod.ticks("fetch(url, timeo", ["url", "timeout", "retries"]),
            {"url": True, "timeout": False, "retries": False})

    def test_substring_does_not_tick(self):
        self.assertEqual(mod.ticks("myurl", ["url"]), {"url": False})

    def test_hostile_fails_closed(self):
        self.assertEqual(mod.ticks(None, None), {})
        self.assertEqual(mod.ticks("x", "url"), {})


class SigslotsSkeletonTest(unittest.TestCase):
    def test_slots_carry_per_param_ticks_and_post_nothing(self):
        out = mod.skeleton_html("s1", SIG)
        self.assertIn("class='sigskel'", out)
        self.assertIn("id='ss-s1'", out)
        for p in ("url", "timeout", "retries"):
            self.assertIn(f"data-param='{p}'", out)
        self.assertIn("[ ]", out)
        self.assertNotIn("<input", out)
        self.assertNotIn("name=", out)  # display only: never posts

    def test_empty_when_off_unparseable_or_parameterless(self):
        self.assertEqual(mod.skeleton_html("s", SIG, enabled=False), "")
        self.assertEqual(mod.skeleton_html("s", "junk"), "")
        self.assertEqual(mod.skeleton_html("s", "f()"), "")
        self.assertEqual(mod.skeleton_html("s", None), "")

    def test_js_ticks_without_submitting(self):
        js = mod.script_js()
        self.assertIn("__sigslotsInit", js)
        self.assertIn(".sigslot", js)
        self.assertIn("input[name=answer]", js)
        self.assertNotIn("submit", js.lower())


class SigslotsCallerEffectTest(unittest.TestCase):
    def test_due_widget_gains_skeleton_with_grading_field_intact(self):
        out = cardsmod.answer_widget(_card(), 0, "/due")
        self.assertIn("sigskel", out)
        self.assertIn("data-param='timeout'", out)
        self.assertIn("__sigslotsInit", out)
        self.assertIn("name='answer'", out)  # grader still reads this
        self.assertIn("Write it", out)

    def test_grading_pinned_pass_fail_unchanged(self):
        ex = {"type": 3, "payload": {"signature": SIG}}
        self.assertTrue(exmod.grade(ex, SIG)["pass"])
        self.assertFalse(exmod.grade(ex, "fetch(url)")["pass"])

    def test_enhance_preserves_body_verbatim(self):
        body = "<input name='answer' size='40'>"
        out = mod.enhance(_card(), body)
        self.assertIn(body, out)  # posted shape untouched

    def test_due_widget_without_signature_is_legacy(self):
        out = cardsmod.answer_widget(_card(signature=""), 0, "/due")
        self.assertNotIn("sigskel", out)
        self.assertNotIn("__sigslotsInit", out)

    def test_enhance_identity_fallback(self):
        body = "<p>legacy</p>"
        self.assertIs(mod.enhance(_card(etype=4), body), body)
        self.assertIs(mod.enhance(_card(signature=""), body), body)
        self.assertIs(mod.enhance(_card(signature="junk"), body), body)


class SigslotsShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["id"], "signature-skeleton")

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
