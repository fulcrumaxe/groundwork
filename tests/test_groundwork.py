"""Groundwork MVP tests (stdlib unittest)."""
import argparse
import io
import json
import subprocess
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest import mock

from groundwork import db as dbmod
from groundwork import diff as diffmod
from groundwork import exercises as ex
from groundwork import graph as graphmod
from groundwork import llm as llmmod
from groundwork import __main__ as mainmod
from groundwork import mcp as mcplib
from groundwork import modules as modmod
from groundwork import pipeline as pipelinemod
from groundwork import sandbox as sbmod
from groundwork import sched as schedmod
from groundwork import select as selectmod


def make_repo():
    tmp = Path(tempfile.mkdtemp(prefix="gw-t-"))
    (tmp / "calc.py").write_text(
        "def add(a=2, b=3):\n    total = a + b\n    return total\n", encoding="utf-8")
    (tmp / "app.ts").write_text(
        "export function greet(name: string): string {\n  return 'hi ' + name;\n}\n",
        encoding="utf-8")
    return tmp


class GraphTest(unittest.TestCase):
    def test_python_parse(self):
        repo = make_repo()
        nodes, edges = graphmod.parse_python_file(repo / "calc.py", repo)
        self.assertTrue(any(n.name == "add" for n in nodes))
        add = next(n for n in nodes if n.name == "add")
        self.assertEqual(add.line, 1)

    def test_ts_parse(self):
        repo = make_repo()
        nodes, _ = graphmod.parse_ts_file(repo / "app.ts", repo)
        self.assertTrue(any(n.name == "greet" for n in nodes))

    def test_ua_adapter(self):
        repo = make_repo()
        ua = repo / ".ua"
        ua.mkdir()
        (ua / "knowledge-graph.json").write_text(json.dumps({
            "nodes": [{"id": "f", "name": "f", "type": "function",
                       "file": "a.py", "line": 3}],
            "edges": [{"from": "f", "to": "g", "type": "calls"}]}), encoding="utf-8")
        g = graphmod.load_ua_graph(ua / "knowledge-graph.json")
        self.assertIn("f", g.nodes)
        self.assertEqual(g.edges[0], ("f", "g", "calls"))

    def test_build_repo_graph(self):
        g = graphmod.build_repo_graph(make_repo())
        self.assertGreaterEqual(len(g.nodes), 2)


class DiffTest(unittest.TestCase):
    def test_parse(self):
        text = ("diff --git a/x.py b/x.py\n@@ -1,2 +1,3 @@\n a\n+b\n c\n")
        d = diffmod.parse_unified_diff(text)
        self.assertEqual(d.files, ["x.py"])
        self.assertEqual(d.hunks[0].start, 1)

    def test_touched_symbols(self):
        repo = make_repo()
        g = graphmod.build_repo_graph(repo)
        d = diffmod.Diff(files=["calc.py"],
                         hunks=[diffmod.Hunk("calc.py", 1, 3, ["x"])])
        hits = diffmod.touched_symbols(d, g)
        self.assertTrue(any("add" in h for h in hits))


class SelectTest(unittest.TestCase):
    def test_rank_and_order(self):
        g = graphmod.Graph()
        g.add(graphmod.Node("a:f", "f", "function", "a.py", 1, complexity=9))
        g.add(graphmod.Node("a:g", "g", "function", "a.py", 10, complexity=1))
        g.edges.append(("a:f", "a:g", "calls"))
        out = selectmod.select_concepts(g, ["a:f", "a:g"],
                                        mastery={"a:g": 1.0}, keep=5)
        self.assertEqual(len(out), 2)
        # prerequisite g first despite lower score
        self.assertEqual(out[0].node_id, "a:g")


class ExerciseTest(unittest.TestCase):
    def setUp(self):
        self.c = selectmod.ScoredConcept("f", "add", "function", "calc.py",
                                         1, 1.0, 1.0, 1.0, 1.0)
        self.snippet = ["def add(a=2, b=3):", "    total = a + b", "    return total"]
        self.runner = sbmod.SandboxRunner()

    def test_all_types_generate(self):
        for t in ex.TYPES:
            ctx = {"runnable": "def add(a=2, b=3):\n    return a + b",
                   "expected_output": "5",
                   "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
                   "trace_var": "total", "trace_expected": ["2", "5"],
                   "buggy": "def add(a=2, b=3):\n    return a - b", "bug_line": 2,
                   "fixed": "def add(a=2, b=3):\n    return a + b",
                   "graph": graphmod.Graph()}
            e = ex.generate(t, f"ex{t}", self.c, self.snippet, ctx)
            self.assertTrue(e["front"], f"type {t} empty front")

    def test_grades(self):
        r = self.runner
        cases = [
            (1, {}, "5", True), (1, {}, "1", False),
            (2, {"answers": ["add"]}, "add", True), (2, {"answers": ["add"]}, "sub", False),
            (4, {"answer": "calc.py"}, "calc.py", True),
            (5, {"rubric": ["add", "calc.py"]}, "add lives in calc.py", True),
            (5, {"rubric": ["add", "zzz", "qqq"]}, "add here", False),
            (13, {"bug_line": 2}, "2", True), (13, {"bug_line": 2}, "3", False),
        ]
        for t, payload, ans, want in cases:
            e = {"id": "x", "type": t, "payload": payload}
            got = ex.grade(e, ans, r)["pass"]
            self.assertEqual(got, want, f"type {t} ans {ans!r}")

    def test_execution_grades(self):
        r = self.runner
        e8 = {"id": "x", "type": 8,
              "payload": {"code": "print(2 + 3)", "expected": "5"}}
        self.assertTrue(ex.grade(e8, "5", r)["pass"])
        self.assertFalse(ex.grade(e8, "6", r)["pass"])
        e9 = {"id": "x", "type": 9,
              "payload": {"code": "x = 1\nx = 2", "var": "x",
                          "expected": ["1", "2"]}}
        self.assertTrue(ex.grade(e9, "1\n2", r)["pass"])
        self.assertFalse(ex.grade(e9, "1\n3", r)["pass"])
        e12 = {"id": "x", "type": 12,
               "payload": {"tests": "assert add() == 5\nprint('OK')",
                           "reference": "def add():\n    return 5"}}
        self.assertTrue(ex.grade(e12, "def add():\n    return 5", r)["pass"])
        self.assertFalse(ex.grade(e12, "def add():\n    return 6", r)["pass"])

    def test_unknown_type(self):
        with self.assertRaises(ValueError):
            ex.generate(99, "x", self.c, self.snippet, {})

    def test_hints_point_at_real_file(self):
        e = ex.generate(1, "ex1", self.c, self.snippet, {})
        self.assertEqual(len(e["hints"]), 3)
        blob = " ".join(e["hints"])
        self.assertNotIn("Guilherme da Silva Pires", blob)
        self.assertIn("calc.py:1", e["hints"][1])

    def _rich_ctx(self):
        g = graphmod.Graph()
        g.add(graphmod.Node("m:main", "main", "function", "calc.py", 10))
        g.add(graphmod.Node("f", "add", "function", "calc.py", 1))
        g.add(graphmod.Node("h", "helper", "function", "calc.py", 5))
        g.add(graphmod.Node("u", "other", "function", "other.py", 1))
        g.edges.append(("m:main", "f", "calls"))
        g.edges.append(("f", "h", "calls"))
        return {"graph": g,
                "decisions": [{"symbol": "add", "chosen": "default args",
                               "rejected": "overloads",
                               "reason": "simpler"}]}

    def test_new_types_generate_grounded(self):
        ctx = self._rich_ctx()
        e7 = ex.generate(7, "ex7", self.c, self.snippet, ctx)
        self.assertTrue(e7["front"])
        self.assertEqual(e7["payload"]["answer"], "default args")
        self.assertTrue(e7["payload"]["grounded"])
        e10 = ex.generate(10, "ex10", self.c, self.snippet, ctx)
        self.assertEqual(e10["payload"]["solution"], ["main", "add", "helper"])
        self.assertTrue(e10["payload"]["grounded"])
        e16 = ex.generate(16, "ex16", self.c, self.snippet, ctx)
        self.assertEqual(e16["payload"]["answer"], "main")
        self.assertIn("main", e16["payload"]["choices"])
        e18 = ex.generate(18, "ex18", self.c, self.snippet, ctx)
        self.assertEqual(e18["payload"]["answer"], "other")
        self.assertEqual(len(e18["payload"]["choices"]), 3)
        self.assertTrue(e18["payload"]["grounded"])

    def test_new_type_grades(self):
        r = self.runner
        e7 = {"id": "x", "type": 7,
              "payload": {"choices": ["a", "b"], "answer": "a"}}
        self.assertTrue(ex.grade(e7, "a", r)["pass"])
        self.assertFalse(ex.grade(e7, "b", r)["pass"])
        e16 = {"id": "x", "type": 16,
               "payload": {"choices": ["m", "f"], "answer": "m"}}
        self.assertTrue(ex.grade(e16, "m", r)["pass"])
        self.assertFalse(ex.grade(e16, "f", r)["pass"])
        e18 = {"id": "x", "type": 18,
               "payload": {"choices": ["m", "h", "o"], "answer": "o"}}
        self.assertTrue(ex.grade(e18, "o", r)["pass"])
        self.assertFalse(ex.grade(e18, "m", r)["pass"])
        e10 = ex.generate(10, "ex10", self.c, self.snippet, self._rich_ctx())
        sol, lines = e10["payload"]["solution"], e10["payload"]["lines"]
        good = " ".join(str(lines.index(s)) for s in sol)
        self.assertTrue(ex.grade({"id": "x", "type": 10,
                                  "payload": e10["payload"]}, good)["pass"])
        bad = ex.grade({"id": "x", "type": 10, "payload": e10["payload"]},
                       "not an order")
        self.assertFalse(bad["pass"])

    def test_docstring_type(self):
        snippet = ["def add(a, b=3):", "    total = a + b", "    return total"]
        e = ex.generate(25, "ex25", self.c, snippet, {})
        self.assertTrue(e["payload"]["grounded"])
        self.assertIn("def add(a, b=3):", e["front"])
        self.assertEqual(e["payload"]["rubric"],
                         ["add", "a", "b", "return"])
        r = self.runner
        self.assertTrue(
            ex.grade({"id": "x", "type": 25, "payload": e["payload"]},
                     "add takes a and b and returns their sum", r)["pass"])
        self.assertFalse(
            ex.grade({"id": "x", "type": 25, "payload": e["payload"]},
                     "something unrelated", r)["pass"])
        # Window above the concept: must not attribute a neighbor's params.
        noisy = ["def helper(x):", "    return x",
                 "def add(a, b=3):", "    return a + b"]
        e2 = ex.generate(25, "ex25b", self.c, noisy, {})
        self.assertIn("b", e2["payload"]["rubric"])
        self.assertNotIn("x", e2["payload"]["rubric"])
        other = ex.generate(25, "ex25c", self.c, ["x = 1"], {})
        self.assertFalse(other["payload"]["grounded"])

    def test_refactor_and_rebuild_grades(self):
        ctx = {"runnable": "def add(a=2, b=3):\n    return a + b",
               "expected_output": "5",
               "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
               "lesson": {"summary": "`add` adds two numbers with defaults."}}
        r = self.runner
        for t in (19, 23):
            e = ex.generate(t, f"ex{t}", self.c, self.snippet, ctx)
            self.assertTrue(e["front"], f"type {t} empty front")
            self.assertTrue(e["payload"]["grounded"], f"type {t} grounded?")
            self.assertTrue(
                ex.grade({"id": "x", "type": t, "payload": e["payload"]},
                         "def add(a=2, b=3):\n    return a + b", r)["pass"])
            self.assertFalse(
                ex.grade({"id": "x", "type": t, "payload": e["payload"]},
                         "def add(a=2, b=3):\n    return 99", r)["pass"])
        e23 = ex.generate(23, "ex23", self.c, self.snippet, ctx)
        self.assertIn("add", e23["payload"]["spec"])
        bare = ex.generate(19, "ex19b", self.c, self.snippet, {})
        self.assertFalse(bare["payload"]["grounded"])

    def _buggy_ctx(self):
        return {
            "runnable": "def add(a=2, b=3):\n    return a + b",
            "expected_output": "5",
            "tests": "_out = repr(add())\nassert _out == '5'\nprint('OK')",
            "buggy": "def add(a=2, b=3):\n    return a - b",
            "bug_line": 2,
            "fixed": "def add(a=2, b=3):\n    return a + b",
            "graph": graphmod.Graph(),
        }

    def test_review_compare_teachback(self):
        ctx = self._buggy_ctx()
        r = self.runner
        e21 = ex.generate(21, "ex21", self.c, self.snippet, ctx)
        self.assertTrue(e21["payload"]["grounded"])
        self.assertEqual(e21["payload"]["bug_line"], 2)
        self.assertTrue(
            ex.grade({"id": "x", "type": 21, "payload": e21["payload"]},
                     "Line 2 in add is wrong: it subtracts", r)["pass"])
        self.assertFalse(
            ex.grade({"id": "x", "type": 21, "payload": e21["payload"]},
                     "Line 1 in add looks fine", r)["pass"])
        e22 = ex.generate(22, "ex22", self.c, self.snippet, ctx)
        self.assertTrue(e22["payload"]["grounded"])
        ans = e22["payload"]["answer"]
        self.assertIn(ans, ("A", "B"))
        self.assertTrue(
            ex.grade({"id": "x", "type": 22, "payload": e22["payload"]},
                     f"{ans}\nbecause the reference passes", r)["pass"])
        wrong = "B" if ans == "A" else "A"
        self.assertFalse(
            ex.grade({"id": "x", "type": 22, "payload": e22["payload"]},
                     wrong, r)["pass"])
        e24 = ex.generate(24, "ex24", self.c, self.snippet, ctx)
        self.assertTrue(e24["payload"]["followups"])
        self.assertTrue(
            ex.grade({"id": "x", "type": 24, "payload": e24["payload"]},
                     "add is a function in calc.py", r)["pass"])
        self.assertFalse(
            ex.grade({"id": "x", "type": 24, "payload": e24["payload"]},
                     "something unrelated here", r)["pass"])

    def test_extend_feature_grades(self):
        ctx = self._buggy_ctx()
        r = self.runner
        e20 = ex.generate(20, "ex20", self.c, self.snippet, ctx)
        self.assertTrue(e20["payload"]["grounded"])
        good = "def add(a=2, b=3, strict=False):\n    return a + b"
        self.assertTrue(
            ex.grade({"id": "x", "type": 20, "payload": e20["payload"]},
                     good, r)["pass"])
        self.assertFalse(
            ex.grade({"id": "x", "type": 20, "payload": e20["payload"]},
                     "def add(a=2, b=3):\n    return a + b", r)["pass"])
        self.assertFalse(
            ex.grade({"id": "x", "type": 20, "payload": e20["payload"]},
                     "def add(a=2, b=3, strict=False):\n    return 99",
                     r)["pass"])
        self.assertFalse(
            ex.grade({"id": "x", "type": 20, "payload": e20["payload"]},
                     "def broken(:", r)["pass"])
        bare = ex.generate(20, "ex20b", self.c, self.snippet, {})
        self.assertFalse(bare["payload"]["grounded"])
        plain = ex.generate(21, "ex21b", self.c, self.snippet, {})
        self.assertFalse(plain["payload"]["grounded"])
        cmp0 = ex.generate(22, "ex22b", self.c, self.snippet, {})
        self.assertFalse(cmp0["payload"]["grounded"])

    def test_new_type_fallbacks_flag_ungrounded(self):
        ctx = {"graph": graphmod.Graph()}
        for t in (7, 10, 18):
            e = ex.generate(t, f"ex{t}", self.c, self.snippet, ctx)
            self.assertTrue(e["front"], f"type {t} empty front")
            self.assertFalse(e["payload"]["grounded"], f"type {t} grounded?")
        e16 = ex.generate(16, "ex16", self.c, self.snippet, ctx)
        self.assertTrue(e16["payload"]["grounded"])
        self.assertEqual(e16["payload"]["answer"], "calc.py")


class SandboxTest(unittest.TestCase):
    def test_run_ok(self):
        r = sbmod.SandboxRunner().run("print(40 + 2)")
        self.assertTrue(r.ok and r.stdout.strip() == "42")

    def test_run_fail(self):
        r = sbmod.SandboxRunner().run("raise SystemExit(1)")
        self.assertFalse(r.ok)

    def test_timeout(self):
        r = sbmod.SandboxRunner(timeout=1).run("while True:\n    pass")
        self.assertFalse(r.ok)
        self.assertIn("timeout", r.stderr)

    def test_trace(self):
        r = sbmod.SandboxRunner().trace("x = 1\nx = 2", "x")
        self.assertTrue(r.ok)
        self.assertEqual(r.data, ["1", "2"])

    def test_verify_filters(self):
        good = {"id": "a", "type": 8, "front": "q",
                "payload": {"code": "print(1)", "expected": "1"}}
        bad = {"id": "b", "type": 8, "front": "q",
               "payload": {"code": "print(1)", "expected": "2"}}
        rep = sbmod.verify_module([good, bad])
        self.assertEqual(len(rep["kept"]), 1)
        self.assertAlmostEqual(rep["pass_rate"], 0.5)


class SchedTest(unittest.TestCase):
    def test_pass_pushes_out_fail_pulls_in(self):
        base = schedmod.review_card(1.0, 0.5, 5)
        again = schedmod.review_card(base["stability"], base["difficulty"], 5)
        fail = schedmod.review_card(5.0, 0.5, 1)
        self.assertGreater(schedmod.parse_iso(again["due"]),
                           schedmod.parse_iso(base["due"]))
        self.assertLess(fail["stability"], 5.0)

    def test_interleave(self):
        cards = [{"concept_id": "a", "exercise_type": "1"},
                 {"concept_id": "a", "exercise_type": "2"},
                 {"concept_id": "b", "exercise_type": "1"}]
        out = schedmod.interleave(cards)
        self.assertEqual(len(out), 3)
        self.assertNotEqual(out[0]["concept_id"], out[1]["concept_id"])


class LLMTest(unittest.TestCase):
    def test_offline_fallback(self):
        import os
        os.environ["GW_NO_LLM"] = "1"
        try:
            p = llmmod.get_provider()
            self.assertIsInstance(p, llmmod.TemplateProvider)
            self.assertIsNone(llmmod.draft_exercises(p, {}, "", [1]))
        finally:
            del os.environ["GW_NO_LLM"]


class MCPTest(unittest.TestCase):
    def test_full_loop(self):
        repo = make_repo()
        db = str(repo / "t.db")
        server = mcplib.MCPServer(db)
        out = server.tool_create_learning_module({
            "repo_path": str(repo), "task_summary": "test",
            "learner_level": "beginner"})
        self.assertGreater(out["exercise_count"], 0)
        self.assertGreaterEqual(out["pass_rate"], 0.9)
        d = server.tool_annotate_decision({"repo": str(repo), "symbol": "add",
                                           "chosen": "default args",
                                           "rejected": "overloads",
                                           "reason": "simpler"})
        self.assertIn("decision_id", d)
        h = server.tool_leave_learning_hole({"repo": str(repo), "file": "calc.py",
                                             "line": 1, "spec": "implement sub"})
        self.assertEqual(h["status"], "open")
        prof = server.tool_get_learner_profile({})
        self.assertIn("unseen", prof)
        due = server.tool_list_due_reviews({})
        self.assertGreater(due["count"], 0)
        # stale detection
        (repo / "calc.py").write_text("def add(a=9, b=9):\n    return a + b\n",
                                      encoding="utf-8")
        con = dbmod.connect(db)
        try:
            n = modmod.mark_stale_cards(con, str(repo))
        finally:
            con.close()
        self.assertGreater(n, 0)

    def test_unknown_tool(self):
        server = mcplib.MCPServer(str(Path(tempfile.mkdtemp()) / "x.db"))
        with self.assertRaises(ValueError):
            server.dispatch("nope", {})

    def test_review_cmd_quits_cleanly(self):
        repo = make_repo()
        db = str(repo / "r.db")
        server = mcplib.MCPServer(db)
        server.tool_create_learning_module({"repo_path": str(repo)})
        ns = argparse.Namespace(db=db, limit=20)
        buf = io.StringIO()
        with mock.patch("builtins.input", return_value="q"):
            with redirect_stdout(buf):
                rc = mainmod.cmd_review(ns)
        self.assertEqual(rc, 0)
        self.assertIn("Reviewed 0 card(s).", buf.getvalue())

    def test_review_cmd_answers_and_grades(self):
        repo = make_repo()
        db = str(repo / "r2.db")
        server = mcplib.MCPServer(db)
        server.tool_create_learning_module({"repo_path": str(repo)})
        ns = argparse.Namespace(db=db, limit=20)
        buf = io.StringIO()
        with mock.patch("builtins.input", side_effect=["5", "4", "q"]):
            with redirect_stdout(buf):
                rc = mainmod.cmd_review(ns)
        self.assertEqual(rc, 0)
        self.assertIn("Reviewed 1 card(s).", buf.getvalue())
        self.assertRegex(buf.getvalue(), "PASS|FAIL")

    def test_review_cmd_empty_queue(self):
        db = str(Path(tempfile.mkdtemp()) / "e.db")
        mcplib.MCPServer(db)
        ns = argparse.Namespace(db=db, limit=20)
        buf = io.StringIO()
        with redirect_stdout(buf):
            rc = mainmod.cmd_review(ns)
        self.assertEqual(rc, 0)
        self.assertIn("Nothing due", buf.getvalue())

    def test_two_modules_share_one_db(self):
        repo = make_repo()
        db = str(repo / "two.db")
        server = mcplib.MCPServer(db)
        first = server.tool_create_learning_module({"repo_path": str(repo)})
        second = server.tool_create_learning_module({"repo_path": str(repo)})
        self.assertGreater(first["exercise_count"], 0)
        self.assertGreater(second["exercise_count"], 0)
        con = dbmod.connect(db)
        try:
            ids = [r[0] for r in con.execute("SELECT id FROM cards").fetchall()]
            mods = [r[0] for r in con.execute("SELECT id FROM modules").fetchall()]
        finally:
            con.close()
        self.assertEqual(len(ids), len(set(ids)))
        self.assertEqual(len(mods), 2)
        self.assertTrue(all(":" in i for i in ids))


class LessonTest(unittest.TestCase):
    def test_docstring_extraction(self):
        repo = make_repo()
        (repo / "doc.py").write_text(
            'def documented():\n    """Does the thing."""\n    return 1\n',
            encoding="utf-8")
        self.assertEqual(
            pipelinemod.docstring_for(repo, "doc.py", 1), "Does the thing.")

    def test_lesson_teaches(self):
        repo = make_repo()
        g = graphmod.build_repo_graph(repo)
        c = selectmod.ScoredConcept("calc.py:add", "add", "function",
                                    "calc.py", 1, 1.0, 1.0, 1.0, 1.0)
        lesson = pipelinemod.lesson_for(repo, c, g)
        self.assertIn("add", lesson["summary"])
        self.assertIn("calc.py", lesson["summary"])
        self.assertTrue(lesson["key_lines"])

    def test_explain_backs_teach(self):
        repo = make_repo()
        db = str(repo / "lesson.db")
        dbmod.init_db(db)
        con = dbmod.connect(db)
        try:
            out = pipelinemod.create_module(
                con, repo=str(repo), task_summary="lesson test",
                learner_level="beginner")
        finally:
            con.close()
        self.assertIn("lessons", out)
        self.assertTrue(out["lessons"])
        for e in out["exercises"]:
            if e["type"] in (1, 5, 6):
                self.assertTrue(e["back"].strip(), f"empty back in {e['id']}")
                self.assertIn(e["concept"], e["back"])
        md = (repo / ".groundwork" / "modules" / f"{out['module_id']}.md").read_text(
            encoding="utf-8")
        self.assertIn("Study guide", md)

    def test_repo_relative_paths(self):
        # Concept files must be repo-relative, never repo-prefixed or absolute.
        repo = make_repo()
        nodes, _ = graphmod.parse_python_file(repo / "calc.py", repo)
        self.assertTrue(all(n.file == "calc.py" for n in nodes))
        g = graphmod.build_repo_graph(repo)
        for n in g.nodes.values():
            self.assertNotIn(repo.name, n.file)
            self.assertFalse(Path(n.file).is_absolute())
            self.assertTrue((repo / n.file).is_file())

    def test_submit_words_to_flashcard_no_crash(self):
        repo = make_repo()
        db = str(repo / "words.db")
        server = mcplib.MCPServer(db)
        out = server.tool_create_learning_module({"repo_path": str(repo)})
        con = dbmod.connect(db)
        try:
            card = con.execute(
                "SELECT id FROM cards WHERE exercise_type='1' LIMIT 1").fetchone()
        finally:
            con.close()
        self.assertIsNotNone(card)
        res = server.submit_review(card["id"], "some words, not a number", 3)
        self.assertIn("result", res)
        self.assertFalse(res["result"]["pass"])

    def test_hole_becomes_exercise(self):
        repo = make_repo()
        db = str(repo / "hole.db")
        server = mcplib.MCPServer(db)
        server.tool_leave_learning_hole({"repo": str(repo), "file": "calc.py",
                                         "line": 1, "spec": "add subtraction"})
        out = server.tool_create_learning_module({"repo_path": str(repo)})
        con = dbmod.connect(db)
        try:
            n = con.execute(
                "SELECT COUNT(*) FROM cards WHERE concept_id LIKE '%hole:%'"
            ).fetchone()[0]
            status = con.execute(
                "SELECT status FROM holes").fetchone()[0]
        finally:
            con.close()
        self.assertGreater(n, 0)
        self.assertEqual(status, "used")

    def test_lesson_shows_source(self):
        repo = make_repo()
        g = graphmod.build_repo_graph(repo)
        c = selectmod.ScoredConcept("calc.py:add", "add", "function",
                                    "calc.py", 1, 1.0, 1.0, 1.0, 1.0)
        lesson = pipelinemod.lesson_for(str(repo), c, g)
        self.assertIn("def add", lesson.get("source", ""))

    def test_four_levels(self):
        from groundwork import explain as explainmod
        lesson = {"concept_id": "c", "name": "add", "kind": "function",
                  "file": "calc.py", "line": 1,
                  "summary": "`add` is a function that returns a + b.",
                  "docstring": "", "callers": ["main"], "callees": [],
                  "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
                  "how": ["Hands back `a + b`."], "worked": None}
        levels = explainmod.levels_for(lesson)
        self.assertEqual([L["n"] for L in levels], [1, 2, 3, 4])
        plain = next(L for L in levels if L["n"] == 1)
        text = " ".join(b["b"] for b in plain["blocks"])
        self.assertIn("function", text)  # glossary box defines the jargon
        expert = next(L for L in levels if L["n"] == 4)
        self.assertTrue(any("Blast radius" in b["h"] for b in expert["blocks"]))

    def test_auto_level(self):
        from groundwork import explain as explainmod
        self.assertEqual(explainmod.auto_level(0.0, 0), 2)  # newcomer
        self.assertEqual(explainmod.auto_level(0.1, 5), 1)  # struggling
        self.assertEqual(explainmod.auto_level(0.5, 5), 2)
        self.assertEqual(explainmod.auto_level(0.8, 5), 3)
        self.assertEqual(explainmod.auto_level(0.95, 9), 4)  # owns it

    def test_level_tabs_render(self):
        from groundwork import web as webmod
        lesson = {"concept_id": "c", "name": "add", "kind": "function",
                  "file": "calc.py", "line": 1, "summary": "Adds.",
                  "docstring": "", "callers": [], "callees": [],
                  "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
                  "how": ["Hands back `a + b`."], "worked": None}
        html_out = webmod.render_levels(lesson, 0.0, 0, "auto", "/")
        for title in ("Plain words", "Beginner", "Intermediate", "Expert"):
            self.assertIn(title, html_out)
        lesson["callers"] = ["main"]
        forced = webmod.render_levels(lesson, 0.95, 9, "4", "/")
        self.assertIn("Blast radius", forced)

    def test_lessons_persisted(self):
        from groundwork import modules as modmod
        repo = make_repo()
        db = str(repo / "persist.db")
        dbmod.init_db(db)
        con = dbmod.connect(db)
        try:
            out = pipelinemod.create_module(
                con, repo=str(repo), task_summary="p", learner_level="beginner")
            row = con.execute("SELECT lessons FROM modules WHERE id=?",
                              (out["module_id"],)).fetchone()
        finally:
            con.close()
        stored = json.loads(row["lessons"])
        self.assertEqual(len(stored), len(out["lessons"]))
        self.assertTrue(all("summary" in L for L in stored))

    def test_walkthrough_explains_steps(self):
        steps = pipelinemod.walkthrough(
            "def add(a=2, b=3):\n    total = a + b\n    return total\n")
        self.assertEqual(len(steps), 2)
        self.assertIn("total", steps[0])
        self.assertIn("Hands back", steps[1])

    def test_worked_example_measured(self):
        repo = make_repo()
        db = str(repo / "worked.db")
        dbmod.init_db(db)
        con = dbmod.connect(db)
        try:
            out = pipelinemod.create_module(
                con, repo=str(repo), task_summary="w", learner_level="beginner")
        finally:
            con.close()
        worked = [L.get("worked") for L in out["lessons"] if L.get("worked")]
        self.assertTrue(worked, "no measured worked example")
        self.assertTrue(worked[0]["output"])

    def test_cloze_multi_blank(self):
        from groundwork import exercises as exmod
        e = {"id": "x", "type": 2,
             "payload": {"blanks": [{"id": 0, "answers": ["add"]},
                                    {"id": 1, "answers": ["total"]}]}}
        self.assertTrue(exmod.grade(e, "0=add\n1=total")["pass"])
        bad = exmod.grade(e, "0=add\n1=wrong")
        self.assertFalse(bad["pass"])
        self.assertIn("1", bad["feedback"])

    def test_match_pairs(self):
        from groundwork import exercises as exmod
        e = {"id": "x", "type": 30,
             "payload": {"pairs": [["add", "calc.py"], ["greet", "app.py"]],
                         "left": ["greet", "add"], "right": ["app.py", "calc.py"],
                         "key": {"0": "A", "1": "B"}}}
        self.assertTrue(exmod.grade(e, "0=A\n1=B")["pass"])
        bad = exmod.grade(e, "0=B\n1=B")
        self.assertFalse(bad["pass"])
        self.assertIn("greet", bad["feedback"])

    def test_mc_choices(self):
        from groundwork import exercises as exmod
        c = selectmod.ScoredConcept("f", "add", "function", "calc.py",
                                    1, 1.0, 1.0, 1.0, 1.0)
        e8 = exmod.generate(8, "ex8", c, ["print(5)"],
                            {"runnable": "print(5)", "expected_output": "5"})
        self.assertIn("5", e8["payload"]["choices"])
        self.assertEqual(len(e8["payload"]["choices"]), 3)
        # Button click submits the choice text: same path as typing it.
        self.assertTrue(exmod.grade(e8, "5", sbmod.SandboxRunner())["pass"])
        self.assertFalse(exmod.grade(e8, "An error is raised",
                                     sbmod.SandboxRunner())["pass"])
        e3 = exmod.generate(3, "ex3", c, ["def add(a, b):"], {})
        self.assertIn("def add(a, b):", e3["payload"]["choices"])

    def test_why_from_entry_time(self):
        from groundwork import pipeline as pipelinemod
        repo = make_repo()
        db = str(repo / "why.db")
        dbmod.init_db(db)
        con = dbmod.connect(db)
        try:
            out = pipelinemod.create_module(
                con, repo=str(repo), task_summary="w", learner_level="beginner",
                purpose="Release blocks on this calc change.",
                concept_notes={"add": "Checkout totals flow through add."})
        finally:
            con.close()
        by_concept: dict[str, list] = {}
        for e in out["exercises"]:
            by_concept.setdefault(e["concept"], []).append(e["why"])
        add_whys = {w for w in by_concept.get("add", [])}
        # Agent's own words, verbatim — nothing templated.
        self.assertTrue(any("Checkout totals" in w for w in add_whys))
        # No repetition: concepts without their own note show no per-card
        # line (the module Mission header carries the purpose once).
        other = {w for c, ws in by_concept.items() if c != "add" for w in ws}
        self.assertEqual(other, {""})
        con = dbmod.connect(db)
        try:
            row = con.execute(
                "SELECT payload FROM cards LIMIT 1").fetchone()
            mission = con.execute(
                "SELECT purpose FROM modules WHERE id=?",
                (out["module_id"],)).fetchone()[0]
        finally:
            con.close()
        import json as _json
        self.assertIn("why", _json.loads(row["payload"]))
        self.assertEqual(mission, "Release blocks on this calc change.")

    def test_why_unstated_not_invented(self):
        from groundwork import pipeline as pipelinemod
        repo = make_repo()
        db = str(repo / "why2.db")
        dbmod.init_db(db)
        con = dbmod.connect(db)
        try:
            out = pipelinemod.create_module(
                con, repo=str(repo), task_summary="w", learner_level="beginner")
        finally:
            con.close()
        self.assertTrue(out["exercises"])
        for e in out["exercises"]:
            self.assertEqual(e["why"], pipelinemod.UNSTATED_WHY)

    def test_describe_tools(self):
        server = mcplib.MCPServer(str(Path(tempfile.mkdtemp()) / "d.db"))
        docs = server.dispatch("describe_tools", {})["tools"]
        self.assertIn("purpose", docs["create_learning_module"]["params"])

    def test_parsons_drag_widget(self):
        from groundwork import web as webmod
        card = {"id": "ex9", "exercise_type": "11",
                "payload": json.dumps({"lines": ["a = 1", "b = 2"],
                                       "solution": ["a = 1", "b = 2"],
                                       "tests": ""})}
        w = webmod.answer_widget(card)
        self.assertIn("draggable", w)
        self.assertIn("answer_text", w)
        self.assertIn("po-ex9", w)

    def test_rich_widgets_render(self):
        from groundwork import web as webmod
        mc = {"id": "c8", "exercise_type": "8",
              "payload": json.dumps({"choices": ["5", "6"], "expected": "5"})}
        self.assertIn("<button", webmod.answer_widget(mc))
        mt = {"id": "c30", "exercise_type": "30",
              "payload": json.dumps({"left": ["add"], "right": ["calc.py"],
                                     "pairs": [["add", "calc.py"]]})}
        w = webmod.answer_widget(mt)
        self.assertIn("m0", w)
        fc = {"id": "c1", "exercise_type": "1", "payload": "{}"}
        self.assertIn("recall", webmod.answer_widget(fc))

    def test_parsons_unrunnable_slice_grades_by_order(self):
        # Bug-hunt find: a correct order failed when the shown slice could
        # not run standalone. Without a harness, order is ground truth.
        from groundwork import exercises as exmod
        e = {"id": "x", "type": 11,
             "payload": {"lines": ["y = f(x)", "x = 1"],
                         "solution": ["x = 1", "y = f(x)"], "tests": ""}}
        self.assertTrue(exmod.grade(e, "1 0")["pass"])
        bad = exmod.grade(e, "0 1")
        self.assertFalse(bad["pass"])
        self.assertIn("Positions", bad["feedback"])

    def test_parsons_positional_feedback(self):
        from groundwork import exercises as exmod
        e = {"id": "x", "type": 11,
             "payload": {"lines": ["b", "a"], "solution": ["a", "b"], "tests": ""}}
        res = exmod.grade(e, "0 1", sbmod.SandboxRunner())
        self.assertFalse(res["pass"])
        self.assertIn("Positions", res["feedback"])


if __name__ == "__main__":
    unittest.main()
