"""Live param checklist beside the extend-feature editor (I-170)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import extlive as mod


def _card(etype, param="strict"):
    return {"id": "x20", "exercise_type": etype,
            "payload": json.dumps({"param": param, "tests": "",
                                   "reference": "pass"})}


class ExtliveUnitTest(unittest.TestCase):
    def test_param_for_reads_payload(self):
        self.assertEqual(mod.param_for(_card(20)), "strict")
        self.assertEqual(mod.param_for(_card(20, "verbose")), "verbose")

    def test_param_for_defaults_like_grade(self):
        self.assertEqual(mod.param_for({"id": "x"}), "strict")
        self.assertEqual(mod.param_for(None), "strict")
        self.assertEqual(
            mod.param_for({"id": "x", "payload": "{bad"}), "strict")

    def test_exists_in_finds_param_anywhere(self):
        self.assertTrue(mod.exists_in("def f(a, strict=False):\n return a\n",
                                      "strict"))
        self.assertTrue(mod.exists_in("def f(a, *args, strict, **kw):\n"
                                      " return a\n", "strict"))
        self.assertFalse(mod.exists_in("def f(a):\n return a\n", "strict"))

    def test_exists_in_never_raises(self):
        self.assertFalse(mod.exists_in("def broken(:", "strict"))
        self.assertFalse(mod.exists_in("", "strict"))
        self.assertFalse(mod.exists_in(None, "strict"))
        self.assertFalse(mod.exists_in("def f():\n pass\n", ""))

    def test_has_default_matches_grader_bar(self):
        self.assertTrue(mod.has_default("def f(a, strict=False):\n return a\n",
                                        "strict"))
        self.assertFalse(mod.has_default("def f(a, strict):\n return a\n",
                                         "strict"))
        self.assertFalse(mod.has_default("def broken(:", "strict"))

    def test_is_used_needs_a_load(self):
        self.assertTrue(mod.is_used("def f(a, strict=False):\n"
                                    " return a if not strict else 1\n",
                                    "strict"))
        self.assertFalse(mod.is_used("def f(a, strict=False):\n return a\n",
                                     "strict"))
        self.assertFalse(mod.is_used("def broken(:", "strict"))

    def test_status_bundles_three_flags(self):
        self.assertEqual(
            mod.status("def f(a, strict=False):\n"
                       " return a if not strict else 1\n", "strict"),
            {"exists": True, "hasdefault": True, "used": True})
        self.assertEqual(mod.status("nope(:", "strict"),
                         {"exists": False, "hasdefault": False,
                          "used": False})

    def test_checklist_renders_unchecked_and_escapes(self):
        out = mod.checklist_html("x20", "strict")
        self.assertEqual(out.count("[ ]"), 3)
        self.assertNotIn("[x]", out)
        self.assertIn("data-param='strict'", out)
        self.assertIn("data-check='exists'", out)
        self.assertIn("data-check='hasdefault'", out)
        self.assertIn("data-check='used'", out)
        evil = mod.checklist_html("x20", "<b>")
        self.assertIn("&lt;b&gt;", evil)
        self.assertNotIn("<b>", evil)

    def test_checklist_empty_is_empty(self):
        self.assertEqual(mod.checklist_html("x20", ""), "")
        self.assertEqual(mod.checklist_html("x20", None), "")

    def test_script_ticks_on_editor_input(self):
        js = mod.script_js()
        self.assertIn("__extliveInit", js)
        self.assertIn(".codeedit-input", js)
        self.assertIn("[x]", js)

    def test_user_visible_strings_are_ascii(self):
        blob = (mod.checklist_html("x1", "strict") + mod.script_js()
                + mod.section_html() + mod.tour_entry()["blurb"])
        self.assertTrue(all(ord(c) < 128 for c in blob), blob[:200])

    def test_section_html_anchors_and_marks_sample(self):
        out = mod.section_html()
        self.assertIn("id='status-b26-extlive'", out)
        self.assertIn("exists=[x]", out)


class ExtliveEffectTest(unittest.TestCase):
    def test_caller_path_gains_checklist_with_legacy_pinned(self):
        # Type-20 Due widget gains the live checklist ...
        out20 = cardsmod.answer_widget(_card(20), 0, "/due")
        self.assertIn("extlive", out20)
        self.assertIn("[ ]", out20)
        self.assertIn("__extliveInit", out20)
        self.assertIn("name='answer'", out20)  # posted field unchanged
        # ... while the sibling code-editor type is byte-identical legacy.
        out12 = cardsmod.answer_widget(_card(12), 0, "/due")
        self.assertNotIn("extlive", out12)
        before = out12
        self.assertEqual(mod.enhance(_card(12), before), before)
