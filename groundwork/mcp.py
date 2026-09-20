"""MCP server: 5 PRD tools over stdio JSON-RPC (and HTTP POST /mcp).

Tools: create_learning_module, annotate_decision, leave_learning_hole,
get_learner_profile, list_due_reviews.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import db as dbmod
from . import exercises as exmod
from . import modules as modmod
from . import pipeline as pipelinemod
from . import sched as schedmod

METHODS = ["create_learning_module", "annotate_decision",
           "leave_learning_hole", "get_learner_profile", "list_due_reviews",
           "describe_tools"]


TOOL_DOCS = {
    "create_learning_module": {
        "purpose": "Build a practice module from a finished agent change.",
        "params": {
            "repo_path": "repo root (required)",
            "commit_range": "e.g. HEAD~1..HEAD; empty = working tree",
            "task_summary": "what the agent just did, one line",
            "touched_symbols": ["node ids or names the change touched"],
            "learner_level": "beginner|intermediate|advanced",
            "purpose": "REQUIRED for a good module: why should the learner "
                       "care about this change? 1-2 sentences, concrete "
                       "(what breaks, what unblocks). Shown on every exercise "
                       "as its reason. Without it each card says no reason "
                       "was given.",
            "concept_notes": {"symbol or node id (e.g. grade, mcp.py:MCPServer.submit_review)":
                              "why THIS symbol matters, one line"},
        },
    },
    "annotate_decision": {"purpose": "Record chose-X-over-Y for rationale exercises.",
                          "params": {"repo": "", "symbol": "", "chosen": "",
                                     "rejected": "", "reason": ""}},
    "leave_learning_hole": {"purpose": "Mark a TODO the learner should write.",
                            "params": {"repo": "", "file": "", "line": 0,
                                       "spec": "what the learner must implement"}},
    "get_learner_profile": {"purpose": "Mastered/weak/unseen concepts.",
                            "params": {"repo": ""}},
    "list_due_reviews": {"purpose": "FSRS due queue.",
                         "params": {"limit": 20}},
}


def _abs_repo(repo: str) -> str:
    try:
        return str(Path(repo or ".").resolve())
    except OSError:
        return repo or ""


class MCPServer:
    def __init__(self, db_path=None):
        self.db_path = Path(db_path or dbmod.DEFAULT_DB)
        dbmod.init_db(self.db_path)

    def _con(self):
        return dbmod.connect(self.db_path)

    def dispatch(self, method: str, params: dict):
        import time
        handler = getattr(self, "tool_" + method, None)
        if handler is None:
            self._log_call(method, False, 0.0)
            raise ValueError(f"unknown tool: {method}")
        start = time.perf_counter()
        try:
            out = handler(params or {})
        except Exception:
            self._log_call(method, False,
                           (time.perf_counter() - start) * 1000.0)
            raise
        if isinstance(out, dict) and out.get("error"):
            self._log_call(method, False,
                           (time.perf_counter() - start) * 1000.0)
        else:
            self._log_call(method, True,
                           (time.perf_counter() - start) * 1000.0)
        return out

    def _log_call(self, method: str, ok: bool, ms: float) -> None:
        """Audit one tool call for the analytics page (F-389)."""
        try:
            con = self._con()
            try:
                con.execute("INSERT INTO tool_calls(method, ok, ms)"
                            " VALUES(?,?,?)", (method, 1 if ok else 0, ms))
                con.commit()
            finally:
                con.close()
        except Exception:  # noqa: BLE001 — analytics never break tools
            pass

    # ------------------------------------------------------------- tools

    def tool_describe_tools(self, p: dict) -> dict:
        return {"tools": TOOL_DOCS}

    def tool_create_learning_module(self, p: dict) -> dict:
        con = self._con()
        try:
            out = pipelinemod.create_module(
                con, repo=p.get("repo_path", "."),
                commit_range=p.get("commit_range", ""),
                task_summary=p.get("task_summary", ""),
                touched_symbols=p.get("touched_symbols", []),
                learner_level=p.get("learner_level", "intermediate"),
                purpose=p.get("purpose", ""),
                concept_notes=p.get("concept_notes", {}))
        finally:
            con.close()
        link = f"/modules/{out['module_id']}"
        return {"module link": link, **{k: v for k, v in out.items() if k != "exercises"},
                "exercise_count": len(out["exercises"])}

    def tool_annotate_decision(self, p: dict) -> dict:
        con = self._con()
        try:
            cur = con.execute(
                "INSERT INTO decisions(repo, symbol, chosen, rejected, reason)"
                " VALUES(?,?,?,?,?)",
                (_abs_repo(p.get("repo", "")), p.get("symbol", ""),
                 p.get("chosen", ""), p.get("rejected", ""),
                 p.get("reason", "")))
            con.commit()
            did = cur.lastrowid
        finally:
            con.close()
        return {"decision_id": did}

    def tool_leave_learning_hole(self, p: dict) -> dict:
        con = self._con()
        try:
            cur = con.execute(
                "INSERT INTO holes(repo, file, line, spec) VALUES(?,?,?,?)",
                (_abs_repo(p.get("repo", "")), p.get("file", ""),
                 int(p.get("line", 0)), p.get("spec", "")))
            con.commit()
            hid = cur.lastrowid
        finally:
            con.close()
        return {"hole_id": hid, "status": "open"}

    def tool_get_learner_profile(self, p: dict) -> dict:
        repo = p.get("repo", "")
        con = self._con()
        try:
            rows = con.execute(
                "SELECT concepts.name, concepts.file, AVG(reviews.grade) AS g,"
                " COUNT(reviews.id) AS n FROM concepts"
                " LEFT JOIN cards ON cards.concept_id = concepts.id"
                " LEFT JOIN reviews ON reviews.card_id = cards.id"
                " GROUP BY concepts.id").fetchall()
        finally:
            con.close()
        mastered = [r["name"] for r in rows if r["n"] and (r["g"] or 0) >= 4.0]
        weak = [r["name"] for r in rows if r["n"] and (r["g"] or 0) < 3.0]
        unseen = [r["name"] for r in rows if not r["n"]]
        _ = repo
        return {"mastered": mastered, "weak": weak, "unseen": unseen}

    def tool_list_due_reviews(self, p: dict) -> dict:
        now = schedmod.iso(schedmod.utcnow())
        con = self._con()
        try:
            rows = con.execute(
                "SELECT cards.*, concepts.name AS concept FROM cards"
                " JOIN concepts ON concepts.id = cards.concept_id"
                " WHERE cards.due <= ? AND cards.stale = 0"
                " ORDER BY cards.due LIMIT ?",
                (now, int(p.get("limit", 20)))).fetchall()
            cards = [dict(r) for r in rows]
        finally:
            con.close()
        return {"due": schedmod.interleave(cards), "count": len(cards)}

    def snooze_card(self, card_id: str) -> dict:
        """Push one card to tomorrow without recording a grade (I-45)."""
        con = self._con()
        try:
            row = con.execute("SELECT id FROM cards WHERE id=?",
                              (card_id,)).fetchone()
            if row is None:
                return {"error": "unknown card"}
            due = schedmod.snooze_due()
            con.execute("UPDATE cards SET due=? WHERE id=?", (due, card_id))
            con.commit()
        finally:
            con.close()
        return {"card_id": card_id, "due": due}

    # ------------------------------------------------------- review/grade

    def submit_review(self, card_id: str, submission: str,
                      confidence: int = 3) -> dict:
        from . import sandbox as sbmod
        con = self._con()
        try:
            row = con.execute("SELECT * FROM cards WHERE id=?", (card_id,)).fetchone()
            if row is None:
                return {"error": "unknown card"}
            card = dict(row)
            exercise = {"id": card["id"], "type": int(card["exercise_type"]),
                        "front": card["front"], "back": card["back"],
                        "payload": json.loads(card["payload"] or "{}")}
            if exercise["type"] == 1:
                result = exmod.grade(exercise, submission)
                try:
                    grade_val = int(str(submission).strip() or 0)
                except ValueError:
                    # Words instead of a 0-5 rating: fail closed with guidance,
                    # never crash the review POST.
                    grade_val = 0
                    result = {"pass": False, "score": 0.0,
                              "feedback": "Enter a recall rating 0-5 first; "
                              "then read the explanation below."}
            else:
                result = exmod.grade(exercise, submission, sbmod.SandboxRunner())
                grade_val = 5 if result["pass"] else 1
            upd = schedmod.review_card(card["stability"], card["difficulty"], grade_val)
            prev_mastery = con.execute(
                "SELECT mastery FROM concepts WHERE id=?",
                (card["concept_id"],)).fetchone()
            con.execute(
                "UPDATE cards SET stability=?, difficulty=?, retrievability=?, due=?"
                " WHERE id=?",
                (upd["stability"], upd["difficulty"], upd["retrievability"],
                 upd["due"], card_id))
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission,"
                " prev_stability, prev_difficulty, prev_retrievability,"
                " prev_due, prev_lapses, prev_mastery)"
                " VALUES(?,?,?,?,?,?,?,?,?,?)",
                (card_id, grade_val, int(confidence), str(submission)[:4000],
                 card["stability"], card["difficulty"], card["retrievability"],
                 card["due"], card["lapses"],
                 (prev_mastery["mastery"] or 0.0) if prev_mastery else 0.0))
            # Roll concept mastery toward latest performance.
            con.execute(
                "UPDATE concepts SET mastery = mastery * 0.7 + ? * 0.3 WHERE id=?",
                (grade_val / 5.0, card["concept_id"]))
            con.commit()
        finally:
            con.close()
        return {"result": result, "grade": grade_val, "next_due": upd["due"]}


def serve_stdio(db_path=None) -> None:
    server = MCPServer(db_path)
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError:
            continue
        mid = msg.get("id")
        try:
            result = server.dispatch(msg.get("method", ""), msg.get("params", {}))
            resp = {"jsonrpc": "2.0", "id": mid, "result": result}
        except Exception as e:  # noqa: BLE001 — must reply, never crash
            resp = {"jsonrpc": "2.0", "id": mid,
                    "error": {"code": -32000, "message": str(e)}}
        sys.stdout.write(json.dumps(resp) + "\n")
        sys.stdout.flush()
