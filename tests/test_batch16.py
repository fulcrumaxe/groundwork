"""Batch 16: generation/rendering integrations (F-57/58/59/60/63/64).

Each engine below used to render only a Status demo no learner path
called. These tests pin the live behavior: generated lessons carry
dual-code packs and retrieval-first levels, and lesson rendering wraps
snippets in predict covers, fades worked steps with practice, asks
self-explanation prompts, and drills elaboration against mastered
siblings.
"""
import unittest

from groundwork import db as dbmod
from groundwork import dualcode as dualmod
from groundwork import elaboration as elabmod
from groundwork import explain as explainmod
from groundwork import graph as graphmod
from groundwork import lessons as lesmod
from groundwork import pipeline as pipelinemod
from groundwork import predict as predictmod
from groundwork import retrieval as retmod
from groundwork import select as selectmod

from test_groundwork import make_repo
from test_web import handler_for, make_module


def _lesson(**kw):
    base = {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1, "summary": "Adds a and b.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["take a", "take b", "return total"], "worked": None,
            "dualcode": {"steps": ["take a", "take b", "return total"],
                         "states": []}}
    base.update(kw)
    return base


def _generated_lesson():
    repo = make_repo()
    g = graphmod.build_repo_graph(str(repo))
    c = selectmod.ScoredConcept("calc.py:add", "add", "function",
                                "calc.py", 1, 1.0, 1.0, 1.0, 1.0)
    return pipelinemod.lesson_for(str(repo), c, g)


def _kinds(blocks):
    return [(("question" if b.get("h") in explainmod.QUESTION_HEADS
              else "prose"), b.get("b", "")) for b in blocks]


class DualcodeGenerationTest(unittest.TestCase):
    def test_lesson_for_stores_diagram_steps(self):
        lesson = _generated_lesson()
        self.assertEqual(lesson["dualcode"]["steps"], lesson["how"])
        self.assertTrue(lesson["how"])
        svg = dualmod.diagram_svg(lesson["dualcode"]["steps"])
        self.assertEqual(svg.count("<rect"), len(lesson["how"]))

    def test_create_module_fills_measured_states(self):
        repo = make_repo()
        db = str(repo / "dual.db")
        dbmod.init_db(db)
        con = dbmod.connect(db)
        try:
            out = pipelinemod.create_module(
                con, repo=str(repo), task_summary="d", learner_level="beginner")
        finally:
            con.close()
        traced = [L for L in out["lessons"]
                  if (L.get("worked") or {}).get("trace")]
        self.assertTrue(traced, "no measured trace to fill states")
        self.assertTrue(traced[0]["dualcode"]["states"])

    def test_render_emits_pack(self):
        html_out = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertIn("dual-diagram", html_out)
        self.assertIn("dual-trace", html_out)
        # Packs nest inside card markup: never an <article> (card counter).
        self.assertNotIn("<article", html_out)

    def test_legacy_lesson_without_steps_renders_no_pack(self):
        lesson = _lesson(how=[], dualcode={"steps": [], "states": []})
        html_out = lesmod.render_levels(lesson, 0.0, 0, "auto", "/")
        self.assertNotIn("dual-pack", html_out)


class RetrievalTemplateTest(unittest.TestCase):
    def test_every_level_retrieves_first(self):
        for level in explainmod.levels_for(_lesson()):
            self.assertEqual(level["blocks"][0]["h"], "Recall first")
            self.assertTrue(retmod.check_order(_kinds(level["blocks"])))

    def test_questions_keep_priority_over_prose(self):
        blocks = [{"h": "Summary", "b": "Adds."},
                  {"h": "Worth probing", "b": "What breaks?"}]
        ordered = explainmod._retrieval_first("add", blocks)
        heads = [b["h"] for b in ordered]
        self.assertEqual(heads[0], "Recall first")
        self.assertLess(heads.index("Worth probing"), heads.index("Summary"))

    def test_empty_and_hostile_input_pass_through(self):
        self.assertEqual(explainmod._retrieval_first("add", []), [])
        self.assertIsNone(explainmod._retrieval_first("add", None))


class PredictCoverTest(unittest.TestCase):
    def test_snippet_hides_under_cover(self):
        html_out = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertIn("class='predict'", html_out)
        self.assertIn("Predict the output, then reveal", html_out)
        self.assertTrue(predictmod.is_covered(
            html_out[html_out.index("<details class='predict'"):]))
        self.assertNotIn("Show me the code", html_out)

    def test_no_source_means_no_cover(self):
        lesson = _lesson(source="", how=[])
        html_out = lesmod.render_levels(lesson, 0.0, 0, "auto", "/")
        self.assertNotIn("class='predict'", html_out)

    def test_language_follows_filename(self):
        self.assertEqual(lesmod._code_lang("app.ts"), "javascript")
        self.assertEqual(lesmod._code_lang("calc.py"), "python")
        self.assertEqual(lesmod._code_lang(""), "python")


class FadingRenderTest(unittest.TestCase):
    def test_new_learner_sees_full_support_only(self):
        html_out = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertNotIn("fade-", html_out)

    def test_practice_fades_partial_then_solo(self):
        once = lesmod.render_levels(_lesson(), 0.0, 1, "auto", "/")
        self.assertIn("fade-partial", once)
        self.assertNotIn("fade-solo", once)
        often = lesmod.render_levels(_lesson(), 0.0, 5, "auto", "/")
        self.assertIn("fade-solo", often)

    def test_no_steps_means_no_faded_section(self):
        html_out = lesmod.render_levels(_lesson(how=[]), 0.0, 4, "auto", "/")
        self.assertNotIn("Faded recall", html_out)


class SelfexplainRenderTest(unittest.TestCase):
    def test_prompts_follow_worked_steps(self):
        html_out = lesmod.render_levels(_lesson(), 0.0, 0, "auto", "/")
        self.assertIn("id='selfexplain'", html_out)
        self.assertEqual(html_out.count("class='selfexplain'"), 3)

    def test_no_steps_means_no_prompts(self):
        html_out = lesmod.render_levels(_lesson(how=[]), 0.0, 0, "auto", "/")
        self.assertNotIn("selfexplain", html_out)


class ElaborationRenderTest(unittest.TestCase):
    OWNED = [{"name": "total", "summary": "running sum accumulator"},
             {"name": "main", "summary": "entry point calling add"}]

    def test_drill_connects_mastered_siblings(self):
        html_out = lesmod.render_levels(_lesson(), 0.9, 9, "auto", "/",
                                        owned=self.OWNED)
        self.assertIn("elaboration drill", html_out)
        self.assertIn("total", html_out)
        self.assertNotIn("<article", html_out)

    def test_no_owned_means_no_drill(self):
        for owned in (None, [], [{"name": "solo", "summary": "only one"}]):
            html_out = lesmod.render_levels(_lesson(), 0.9, 9, "auto", "/",
                                            owned=owned)
            self.assertNotIn("elaboration drill", html_out)

    def test_owned_helper_takes_top_tier_siblings(self):
        lesson_map = {"a": {"name": "a"}, "b": {"name": "b"},
                      "c": {"name": "c"}}
        mastery_of = {"a": 0.9, "b": 0.4, "c": 0.85}
        owned = lesmod.owned_lessons(lesson_map, mastery_of, "a")
        self.assertEqual([o["name"] for o in owned], ["c"])
        self.assertEqual(lesmod.owned_lessons({}, {}, "a"), [])
        self.assertEqual(lesmod.owned_lessons(None, None, "a"), [])


class LessonPageTest(unittest.TestCase):
    def test_due_page_covers_snippets_and_recalls_first(self):
        _tmp, db, _server, _out = make_module("batch16 lesson page")
        body = handler_for(db).due_html()
        self.assertIn("class='predict'", body)
        self.assertIn("Recall first", body)

    def test_module_page_renders_packs_without_drill_for_newcomer(self):
        _tmp, db, _server, out = make_module("batch16 module page")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("dual-diagram", body)
        self.assertNotIn("elaboration drill", body)


if __name__ == "__main__":
    unittest.main()
