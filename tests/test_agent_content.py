"""Caller-authored module content: the agent that made the change writes
the lessons, the pipeline only fills gaps. Covers pipeline.apply_agent_lessons,
pipeline.build_agent_exercises, and the MCP pass-through."""
import json
import unittest

from groundwork import db as dbmod

from test_web import make_module


def _db(db_path):
    return dbmod.connect(db_path)


class AgentContentTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("agent content")
        self.concept = self.out["concepts"][0]

    def _create(self, **kw):
        params = {"repo_path": str(self.tmp), "task_summary": "agent words"}
        params.update(kw)
        return self.server.tool_create_learning_module(params)

    def test_agent_lesson_overrides_template(self):
        out = self._create(lessons=[{
            "concept": self.concept,
            "summary": "AGENT WORDS: add() defaults keep callers honest.",
            "how": ["Read the defaults", "Trace the total"],
        }])
        self.assertEqual(out.get("agent_errors"), [])
        con = _db(self.db)
        try:
            row = con.execute(
                "SELECT lessons FROM modules WHERE id=?",
                (out["module_id"],)).fetchone()
            lessons = json.loads(row["lessons"])
        finally:
            con.close()
        mine = [L for L in lessons if L.get("agent")]
        self.assertEqual(len(mine), 1)
        self.assertIn("AGENT WORDS", mine[0]["summary"])
        self.assertEqual(mine[0]["how"], ["Read the defaults", "Trace the total"])

    def test_agent_exercise_persisted_as_card(self):
        out = self._create(exercises=[{
            "concept": self.concept, "type": 1,
            "front": "AGENT Q: why do the defaults matter?",
            "back": "AGENT A: they keep callers honest.",
        }])
        self.assertEqual(out.get("agent_errors"), [])
        con = _db(self.db)
        try:
            row = con.execute(
                "SELECT front, back FROM cards WHERE front LIKE 'AGENT Q%'"
            ).fetchone()
        finally:
            con.close()
        self.assertIsNotNone(row)
        self.assertIn("AGENT A", row["back"])

    def test_bad_items_collected_not_silent(self):
        out = self._create(
            lessons=[{"concept": "nope:missing"},
                     {"concept": self.concept}],
            exercises=[{"concept": "nope:missing", "front": "q", "back": "a"},
                       {"concept": self.concept, "front": "q"},
                       {"concept": self.concept, "type": 999,
                        "front": "q", "back": "a"}])
        self.assertIn("module_id", out)  # module still lands
        errs = out.get("agent_errors", [])
        self.assertEqual(len(errs), 5)
        self.assertTrue(any("unknown concept" in e for e in errs))
        self.assertTrue(any("missing summary" in e for e in errs))
        self.assertTrue(any("front and back" in e for e in errs))
        self.assertTrue(any("unknown type" in e for e in errs))

    def test_non_list_params_rejected(self):
        self.assertIn("error", self._create(lessons="just words"))
        self.assertIn("error", self._create(exercises={"front": "q"}))

    def test_agent_exercises_only_replaces_trivia(self):
        out = self._create(
            exercises=[{"concept": self.concept, "type": 1,
                        "front": "AGENT Q: what?", "back": "AGENT A: this."}],
            agent_exercises_only=True)
        self.assertEqual(out.get("agent_errors"), [])
        con = _db(self.db)
        try:
            fronts = [r["front"] for r in con.execute(
                "SELECT front FROM cards JOIN concepts "
                "ON concepts.id = cards.concept_id "
                "WHERE concepts.module_id = ?", (out["module_id"],)).fetchall()]
        finally:
            con.close()
        self.assertTrue(fronts)
        self.assertTrue(all(f.startswith("AGENT Q") for f in fronts),
                        fronts)

    def test_agent_exercises_only_falls_back(self):
        out = self._create(
            exercises=[{"concept": self.concept, "type": 999,
                        "front": "q", "back": "a"}],
            agent_exercises_only=True)
        self.assertTrue(any("fallback" in e for e in out["agent_errors"]))
        con = _db(self.db)
        try:
            n = con.execute("SELECT COUNT(*) AS n FROM cards").fetchone()["n"]
        finally:
            con.close()
        self.assertGreater(n, 0)


if __name__ == "__main__":
    unittest.main()
