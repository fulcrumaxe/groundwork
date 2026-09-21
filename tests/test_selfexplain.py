"""Self-explanation prompts after every worked step (F-58)."""
import unittest

from groundwork import selfexplain as semod


class SelfExplainPromptsTest(unittest.TestCase):
    def test_per_step_count_and_index(self):
        steps = ["Bind the socket.", "Listen for one client.", "Accept and reply."]
        got = semod.selfexplain_prompts(steps)
        self.assertEqual(len(got), len(steps))
        self.assertEqual([g["step"] for g in got], [0, 1, 2])
        for g in got:
            self.assertTrue(g["prompt"])

    def test_templates_rotate_by_index(self):
        import re
        steps = [f"line {i}" for i in range(7)]
        prompts = [g["prompt"] for g in semod.selfexplain_prompts(steps)]
        # Templates embed the step number: compare with numbers out so
        # rotation (period 3), not numbering, is what gets asserted.
        shapes = [re.sub(r"\d+", "#", p) for p in prompts]
        self.assertEqual(shapes[0], shapes[3])  # period == len(TEMPLATES)
        self.assertNotEqual(shapes[0], shapes[1])
        self.assertNotEqual(shapes[1], shapes[2])
        # ... while the numbers themselves still count up per step.
        for i, p in enumerate(prompts):
            self.assertIn(f"step {i + 1}", p.lower())
            self.assertIn("step", p.lower())

    def test_empty_and_hostile_input_fail_closed(self):
        for bad in ([], (), None, "", 42, object(), {"step": 0}):
            self.assertEqual(semod.selfexplain_prompts(bad), [])
        # Dirty entries skip without echoing raw input
        got = semod.selfexplain_prompts(["ok line", None, 7, "   ", "<b>x</b>"])
        self.assertEqual([g["step"] for g in got], [0, 4])
        self.assertNotIn("<b>x</b>", repr(got))

    def test_prompts_html_escapes(self):
        html = semod.prompts_html([{"step": 0, "prompt": "<script>alert(1)</script>"}])
        self.assertNotIn("<script>", html)
        self.assertIn("&lt;script&gt;", html)
        self.assertIn("<details", html)
        self.assertIn("<summary>", html)

    def test_prompts_html_empty_and_hostile(self):
        for bad in ([], None, "", 42, object(), [{"nope": 1}, {"prompt": "  "}, "str"]):
            self.assertEqual(semod.prompts_html(bad), "")

    def test_section_html_anchor(self):
        html = semod.section_html()
        self.assertIn("id='status-b12-selfexplain'", html)

    def test_tour_entry_shape(self):
        e = semod.tour_entry()
        self.assertEqual(e["id"], "self-explain")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["title"], "Self-explanation prompts")
        self.assertTrue(e["blurb"])
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], "status-b12-selfexplain")

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "selfexplain.py").read_text(encoding="utf-8")
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
