"""Caller-authored module content: the agent that made the change writes
every lesson and exercise; the pipeline never fills gaps.

Covers pipeline.create_module's coverage gate: a module lands if and only
if every selected concept carries an agent-authored lesson (summary in the
caller's own words) and at least one agent-authored exercise. Generated
lessons, generated cards, LLM drafts, and template fallbacks do not exist —
only sandbox measurement (worked examples, card verification) may add to
what the caller wrote.
"""
import unittest

from groundwork import db as dbmod

from test_groundwork import make_repo
from test_web import make_module


def _db(db_path):
    return dbmod.connect(db_path)


LESSONS = [
    {"concept": "add",
     "summary": "AGENT WORDS: add() defaults keep callers honest.",
     "how": ["Read the defaults", "Trace the total"]},
    {"concept": "greet",
     "summary": "AGENT WORDS: greet() prefixes any name with hi.",
     "how": ["Read the name", "Prefix hi"]},
]

EXERCISES = [
    {"concept": "add", "type": 1,
     "front": "AGENT Q: why do the defaults matter?",
     "back": "AGENT A: they keep callers honest."},
    {"concept": "greet", "type": 1,
     "front": "AGENT Q: what does greet return for bob?",
     "back": "AGENT A: hi bob."},
]


class AgentContentTest(unittest.TestCase):
    def setUp(self):
        self.repo = make_repo()
        self.db = str(self.repo / "agent.db")
        dbmod.init_db(self.db)
        from groundwork import mcp as mcplib
        self.server = mcplib.MCPServer(self.db)

    def _create(self, **kw):
        params = {"repo_path": str(self.repo), "task_summary": "agent words"}
        params.update(kw)
        return self.server.tool_create_learning_module(params)

    def _module_count(self):
        con = _db(self.db)
        try:
            return con.execute("SELECT COUNT(*) AS n FROM modules").fetchone()["n"]
        finally:
            con.close()

    def test_missing_lessons_rejected(self):
        out = self._create(exercises=EXERCISES)
        self.assertIn("error", out)
        self.assertNotIn("module_id", out)
        self.assertEqual(self._module_count(), 0)

    def test_lesson_gap_rejected(self):
        out = self._create(lessons=LESSONS[:1], exercises=EXERCISES)
        self.assertIn("error", out)
        self.assertNotIn("module_id", out)
        self.assertIn("greet", out["error"])
        self.assertEqual(self._module_count(), 0)

    def test_missing_exercises_rejected(self):
        out = self._create(lessons=LESSONS)
        self.assertIn("error", out)
        self.assertNotIn("module_id", out)
        self.assertEqual(self._module_count(), 0)

    def test_exercise_gap_rejected(self):
        out = self._create(lessons=LESSONS, exercises=EXERCISES[:1])
        self.assertIn("error", out)
        self.assertNotIn("module_id", out)
        self.assertIn("greet", out["error"])
        self.assertEqual(self._module_count(), 0)

    def test_full_coverage_lands_agent_only(self):
        for flag in (False, True):  # legacy flag changes nothing now
            out = self._create(lessons=LESSONS, exercises=EXERCISES,
                               agent_exercises_only=flag)
            self.assertEqual(out.get("agent_errors"), [], out)
        con = _db(self.db)
        try:
            lessons = con.execute("SELECT lessons FROM modules").fetchall()
            fronts = [r["front"] for r in con.execute("SELECT front FROM cards").fetchall()]
        finally:
            con.close()
        self.assertTrue(fronts)
        self.assertTrue(all(f.startswith("AGENT Q") for f in fronts), fronts)

    def test_bad_items_reported_not_silent(self):
        out = self._create(
            lessons=[{"concept": "nope:missing"},
                     {"concept": "add"},
                     {"concept": "greet", "summary": "s"}],
            exercises=[{"concept": "nope:missing", "front": "q", "back": "a"},
                       {"concept": "add", "front": "q"},
                       {"concept": "add", "type": 999,
                        "front": "q", "back": "a"}])
        self.assertIn("error", out)  # add/greet coverage never completed
        self.assertNotIn("module_id", out)
        errs = out.get("agent_errors", [])
        self.assertTrue(any("unknown concept" in e for e in errs))
        self.assertTrue(any("missing summary" in e for e in errs))
        self.assertTrue(any("front and back" in e for e in errs))
        self.assertTrue(any("unknown type" in e for e in errs))

    def test_non_list_params_rejected(self):
        self.assertIn("error", self._create(lessons="just words"))
        self.assertIn("error", self._create(exercises={"front": "q"}))

    def test_unverifiable_cards_leave_no_empty_module(self):
        out = self._create(
            lessons=LESSONS,
            exercises=[
                {"concept": "add", "type": 8,
                 "front": "AGENT Q: what prints?",
                 "back": "AGENT A: 2.",
                 "payload": {"code": "print(1)", "expected": "2"}},
                {"concept": "greet", "type": 8,
                 "front": "AGENT Q: what prints?",
                 "back": "AGENT A: 2.",
                 "payload": {"code": "print(1)", "expected": "2"}},
            ])
        self.assertIn("error", out)
        self.assertNotIn("module_id", out)
        self.assertEqual(self._module_count(), 0)

    def test_single_concept_fixture_covers_itself(self):
        _tmp, db, server, out = make_module("agent content")
        self.assertIn("module_id", out)
        self.assertEqual(out.get("agent_errors"), [])


if __name__ == "__main__":
    unittest.main()
