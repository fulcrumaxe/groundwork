"""Try-it-yourself micro-prompts between study paragraphs (I-112)."""
import unittest

from groundwork import lessons as lesmod
from groundwork import tryprompts as trymod


def _blocks():
    return [
        {"h": "What it does", "b": "An adder combines two numbers."},
        {"h": "How it works", "b": "First take a, then take b, then sum."},
        {"h": "Worked example", "b": "add(2, 3) gives 5."},
    ]


class PromptsForTest(unittest.TestCase):
    def test_one_prompt_per_eligible_block_except_last(self):
        got = trymod.prompts_for(_blocks())
        self.assertEqual([g["after"] for g in got], [0, 1])
        for g in got:
            self.assertTrue(g["prompt"])

    def test_skips_questions_code_and_hostile(self):
        blocks = [{"h": "Recall first", "b": "From memory, what does it do?"},
                  {"h": "Source", "b": "def add(a, b): ...", "pre": True},
                  {"h": "What it does", "b": "Adds."},
                  {"h": "Tail", "b": "Last one."}]
        got = trymod.prompts_for(blocks)
        self.assertEqual([g["after"] for g in got], [2])
        for bad in ([], (), None, "", 42, object(), {"after": 0}):
            self.assertEqual(trymod.prompts_for(bad), [])
        self.assertEqual(trymod.prompts_for([None, 7, "  ", "<b>x</b>"]), [])

    def test_templates_rotate(self):
        import re
        ps = [trymod.prompt_for(i) for i in range(7)]
        shapes = [re.sub(r"\d+", "#", p) for p in ps]
        self.assertEqual(shapes[0], shapes[3])
        self.assertNotEqual(shapes[0], shapes[1])
        self.assertEqual(trymod.prompt_for("junk"), trymod.TEMPLATES[0])


class HtmlTest(unittest.TestCase):
    def test_block_prompt_html_escapes_and_fails_closed(self):
        html = trymod.block_prompt_html(0, {"h": "What it does", "b": "Adds."})
        self.assertIn("Try it yourself", html)
        self.assertIn("<details", html)
        self.assertEqual(trymod.block_prompt_html(
            0, {"h": "Recall first", "b": "q?"}), "")
        self.assertEqual(trymod.block_prompt_html(
            0, {"h": "Source", "b": "code", "pre": True}), "")
        self.assertEqual(trymod.block_prompt_html(
            0, {"h": "X", "b": "<script>alert(1)</script>"}).count("<script>"), 0)

    def test_prompts_html_empty_and_hostile(self):
        for bad in ([], None, "", 42, object(),
                     [{"nope": 1}, {"prompt": "  "}, "str"]):
            self.assertEqual(trymod.prompts_html(bad), "")
        html = trymod.prompts_html([{"after": 0, "prompt": "Try: restate it."}])
        self.assertIn("id='tryprompts'", html)


class CallerPathTest(unittest.TestCase):
    def _lesson(self):
        return {"name": "add", "kind": "function", "file": "calc.py",
                "line": 1, "summary": "Adds two numbers together.",
                "docstring": "", "how": ["Take a.", "Take b.", "Sum them."],
                "source": "", "callers": [], "callees": []}

    def test_render_levels_interleaves_prompts(self):
        body = lesmod.render_levels(self._lesson(), 0.0, 1, "auto",
                                    "/modules/m1")
        self.assertIn("tryprompt", body)
        self.assertGreater(body.index("Try it yourself"), body.index("<h5>"))

    def test_no_prompt_after_last_block(self):
        body = lesmod.render_levels(self._lesson(), 0.0, 1, "auto",
                                    "/modules/m1")
        tail = body.rsplit("</details>", 1)[-1]
        self.assertNotIn("tryprompt", tail)

    def test_legacy_fallback_no_eligible_blocks(self):
        from groundwork import explain as explainmod
        real = explainmod.levels_for
        try:
            explainmod.levels_for = lambda lesson: [
                {"n": 2, "title": "Beginner",
                 "blocks": [{"h": "Recall first", "b": "From memory?"}],
                 "code": ""},
                {"n": 1, "title": "Plain words", "blocks": [],
                 "code": ""},
                {"n": 3, "title": "Intermediate", "blocks": [],
                 "code": ""},
                {"n": 4, "title": "Expert", "blocks": [], "code": ""}]
            body = lesmod.render_levels(self._lesson(), 0.0, 0, "2",
                                        "/modules/m1")
            self.assertNotIn("tryprompt", body)
            self.assertNotIn("Try it yourself", body)
        finally:
            explainmod.levels_for = real

    def test_section_anchor_and_tour_shape(self):
        self.assertIn("id='status-b19-tryprompts'", trymod.section_html())
        e = trymod.tour_entry()
        self.assertEqual(e["id"], "try-prompts")
        self.assertEqual(e["path"], "/modules/{mid}")
        self.assertEqual(e["anchor"], "{lesson}")
        self.assertTrue(e["blurb"])

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "tryprompts.py").read_text(encoding="utf-8")
        for marker in ("TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
