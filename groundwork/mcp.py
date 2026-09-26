"""MCP server: 5 PRD tools over stdio JSON-RPC (and HTTP POST /mcp).

Tools: create_learning_module, annotate_decision, leave_learning_hole,
get_learner_profile, list_due_reviews.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

from . import calibdrill as drillmod
from . import confweight as confweightmod
from . import db as dbmod
from . import diffvote as diffvotemod
from . import diffweights as diffweightsmod
from . import boredom as boredommod
from . import exercises as exmod
from . import frustcatch as frustcatchmod
from . import interleave as interleavemod
from . import katabank as katabankmod
from . import lessondeps as lessondepsmod
from . import lessons as lesmod
from . import modules as modmod
from . import ownership as ownmod
from . import retest as retestmod
from . import remedpath as remedpathmod
from . import giveup as giveupmod
from . import partial as partialmod
from . import retryblanks as retryblanksmod
from . import reveal as revealmod
from . import skillatoms as skillatomsmod
from . import pipeline as pipelinemod
from . import sched as schedmod
from . import sleepsched as sleepschedmod

METHODS = ["create_learning_module", "annotate_decision",
           "leave_learning_hole", "get_learner_profile", "list_due_reviews",
           "describe_tools"]


TOOL_DOCS = {
    "create_learning_module": {
        "purpose": "Build a practice module from a finished agent change. "
                   "You (the agent that made the change) write everything: "
                   "every selected concept needs your lesson and at least "
                   "one of your exercises, or the call fails and nothing "
                   "is stored. Nothing is generated or gap-filled.",
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
            "lessons": [{"concept": "REQUIRED, one per selected concept: node id or name",
                         "summary": "REQUIRED: what the learner should understand, in your own words",
                         "how": ["optional: how it works, step by step"],
                         "key_lines": "optional: the lines that matter"}],
            "exercises": [{"concept": "REQUIRED, at least one per selected concept",
                           "type": "exercise id 1-48 (default 1)",
                           "front": "REQUIRED: the question, in your own words",
                           "back": "REQUIRED: the answer, in your own words"}],
            "agent_exercises_only": "legacy, accepted and ignored: every card is caller-authored",
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
                concept_notes=p.get("concept_notes", {}),
                agent_lessons=p.get("lessons"),
                agent_exercises=p.get("exercises"),
                agent_exercises_only=bool(p.get("agent_exercises_only", False)))
        finally:
            con.close()
        if out.get("error"):
            return out
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

    # Probes per listing: extra credit after the real queue, never
    # displacing it. Capped so a long-owned library cannot flood Due.
    PROBE_CAP = 5

    def _probe_cards(self, con, now_iso: str) -> list:
        """Owned/stable cards due for a 7/30-day probe (Batch 15, F-51).

        Assembles engine dicts (owned via ownership.owned_map,
        last_review from reviews, last_probe from the Batch 15 column)
        and returns full card rows flagged probe=7|30, most overdue
        first. Never raises; anything unreadable means no probes.
        """
        try:
            rows = con.execute(
                "SELECT cards.*, concepts.name AS concept,"
                " concepts.module_id AS module_id,"
                " (SELECT MAX(reviewed_at) FROM reviews"
                " WHERE card_id = cards.id) AS last_review"
                " FROM cards JOIN concepts ON concepts.id = cards.concept_id"
                " WHERE cards.stale = 0 AND cards.stability >= 7.0").fetchall()
            cands = [dict(r) for r in rows]
            if not cands:
                return []
            omaps: dict = {}
            for c in cands:
                mid = c.get("module_id") or ""
                if mid not in omaps:
                    try:
                        omaps[mid] = ownmod.owned_map(con, mid)
                    except Exception:  # noqa: BLE001 -- no map, no probes
                        omaps[mid] = {}
            eng = []
            for c in cands:
                if not c.get("last_review"):
                    continue
                attempts, owned = omaps.get(
                    c.get("module_id") or "", {}).get(
                    c.get("concept_id"), (0, False))
                if not owned:
                    continue
                eng.append({"id": c["id"], "card_id": c["id"], "owned": True,
                            "stability": c.get("stability"),
                            "last_review": c.get("last_review"),
                            "last_probe": c.get("last_probe")})
            hits = retestmod.probes_due(eng, now_iso)
            by_id = {c["id"]: c for c in cands}
            out = []
            for h in hits[:self.PROBE_CAP]:
                c = by_id.get(h["card_id"])
                if c is None:
                    continue
                flagged = dict(c)
                flagged["probe"] = h["window"]
                out.append(flagged)
            return out
        except Exception:  # noqa: BLE001 -- probes must never break Due
            return []

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
            mrows = con.execute(
                "SELECT cards.concept_id, cards.exercise_type,"
                " AVG(reviews.grade) AS g, COUNT(reviews.id) AS n"
                " FROM cards LEFT JOIN reviews"
                " ON reviews.card_id = cards.id"
                " GROUP BY cards.concept_id, cards.exercise_type").fetchall()
            mastery = {(r["concept_id"], r["exercise_type"]): r["g"]
                       for r in mrows if r["n"]}
            # F-87: per-smell kata history; empty keeps the legacy order.
            krows = con.execute(
                "SELECT reviews.grade, reviews.reviewed_at, cards.payload"
                " FROM reviews JOIN cards ON cards.id = reviews.card_id").fetchall()
            kata_history = katabankmod.kata_history_from_rows(krows)
            probes = self._probe_cards(con, now)
            known = {c["id"] for c in cards}
            cards = cards + [p for p in probes if p["id"] not in known]
            seen = {r[0] for r in con.execute(
                "SELECT DISTINCT card_id FROM reviews").fetchall()}
            try:
                grows = con.execute(
                    "SELECT cards.concept_id, reviews.grade FROM reviews"
                    " JOIN cards ON cards.id = reviews.card_id"
                    " ORDER BY reviews.id").fetchall()
            except Exception:  # noqa: BLE001 -- no history, no promotion
                grows = []
            # F-100: prerequisite map (lesson needs per concept) plus
            # concept mastery on the scheduler's grade scale.
            try:
                remap: dict = {}
                for (lj,) in con.execute(
                        "SELECT lessons FROM modules").fetchall():
                    try:
                        lessons = json.loads(lj or "[]")
                    except ValueError:
                        continue
                    for lesson in lessons:
                        if isinstance(lesson, dict) and lesson.get("concept_id"):
                            needs = lessondepsmod.needs_of(lesson)
                            if needs:
                                remap.setdefault(lesson["concept_id"], needs)
                remaster: dict = {}
                for r in con.execute(
                        "SELECT id, name, mastery FROM concepts").fetchall():
                    grade = (r["mastery"] or 0.0) * 5.0
                    remaster[r["id"]] = grade
                    if r["name"]:
                        remaster[r["name"]] = grade
                        remaster[lesmod.slug(r["name"])] = grade
            except Exception:  # noqa: BLE001 -- no map, no remediation
                remap, remaster = {}, {}
        finally:
            con.close()
        ordered = katabankmod.order_due(
            interleavemod.order_due(cards, mastery), kata_history)
        # F-93: new cards never display a night due; reviewed cards keep
        # their stored due, queue order untouched (applied post-ordering).
        ordered = sleepschedmod.defer_night_new(ordered, reviewed_ids=seen)
        # F-97: bored concepts surface their next-rung card first;
        # calm queues keep today's order.
        hist: dict = {}
        for cid, grade in grows:
            hist.setdefault(cid, []).append(grade)
        ordered = boredommod.promote(
            ordered, {cid: grades[-boredommod.HISTORY_TAIL:]
                      for cid, grades in hist.items()})
        # I-146: difficulty votes reweight voted concepts' cards;
        # no votes keeps today's order (empty tallies fall back).
        try:
            cids = [c.get("concept_id") for c in ordered
                    if isinstance(c, dict)]
            ordered = diffweightsmod.order_due(
                ordered, diffvotemod.tallies(self.db_path, cids))
        except Exception:  # noqa: BLE001 -- votes never break the queue
            pass
        # F-100: a failed concept pulls its unmastered prerequisites
        # ahead of the retry; calm queues keep today's order.
        try:
            latest: dict = {}
            for cid, grade in grows:
                latest[cid] = grade
            failures = [cid for cid, g in latest.items()
                        if g is not None and g < 3]
            bykey: dict = {}
            for c in ordered:
                bykey.setdefault(c.get("concept_id") or "", c)
                name = c.get("concept") or ""
                bykey.setdefault(name, c)
                bykey.setdefault(lesmod.slug(name), c)
            pmap = {}
            for failed in failures:
                have = [n for n in remap.get(failed, [])
                        if n in bykey or lesmod.slug(n) in bykey]
                if have:
                    pmap[failed] = have
            if pmap:
                lift = set()
                for needs in pmap.values():
                    for need in needs:
                        hit = bykey.get(need) \
                            or bykey.get(lesmod.slug(need))
                        if isinstance(hit, dict) and hit.get("id"):
                            lift.add(hit["id"])

                def _maker(concept, failed, _by=bykey):
                    found = _by.get(concept) \
                        or _by.get(lesmod.slug(concept)) or {}
                    card = dict(found)
                    card["remedial"] = True
                    card["remediation_for"] = failed
                    return card

                rest = [c for c in ordered if c.get("id") not in lift]
                ordered = remedpathmod.queue_remediation(
                    rest, failures, pmap, remaster, make_card=_maker)
        except Exception:  # noqa: BLE001 -- remediation never blocks
            pass
        return {"due": ordered, "count": len(cards)}

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
            # I-158/I-159: surrender logs grade 0 (reveal) and
            # records a lapse (giveup); downstream scheduling and
            # History inserts run unchanged.
            new_lapses = card["lapses"]
            if revealmod.is_reveal_request(submission, confidence):
                new_lapses = giveupmod.next_lapses(card["lapses"])
                result = revealmod.reveal_result(card)
                result["feedback"] += " " + giveupmod.lapse_line(new_lapses)
                grade_val = 0
            elif exercise["type"] == 1:
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
            # I-160/I-161: missed cloze names which blanks passed
            # and offers a retry of the wrong ones only; clean cards
            # and surrender feedback render exactly as before.
            retry_html = ""
            if (exercise["type"] == 2 and not result.get("pass")
                    and not result.get("revealed")):
                rows = partialmod.per_blank(exercise["payload"], submission)
                missed = [r["id"] for r in rows if not r.get("passed")]
                if rows and missed:
                    result["feedback"] += " " + partialmod.summary_line(rows)
                    retry_html = retryblanksmod.retry_form(
                        {"id": card_id, "payload": exercise["payload"]},
                        submission, wrong_ids=missed)
            hist = [r[0] for r in con.execute(
                "SELECT grade FROM reviews WHERE card_id=? ORDER BY rowid",
                (card_id,)).fetchall()]
            upd = schedmod.review_card(card["stability"], card["difficulty"],
                                       grade_val, grades=hist + [grade_val])
            # F-93: a first review landing in quiet hours defers to
            # morning so new cards are never scheduled late at night.
            if not hist:
                upd["due"] = sleepschedmod.adjust_due(upd["due"])
            prev_mastery = con.execute(
                "SELECT mastery FROM concepts WHERE id=?",
                (card["concept_id"],)).fetchone()
            # Batch 15, F-51: was this answer a probe? Pre-state only —
            # the current review must not cover its own cycle.
            try:
                pre_review = con.execute(
                    "SELECT MAX(reviewed_at) FROM reviews WHERE card_id=?",
                    (card_id,)).fetchone()[0]
                mod_row = con.execute(
                    "SELECT module_id FROM concepts WHERE id=?",
                    (card["concept_id"],)).fetchone()
                try:
                    omap = ownmod.owned_map(
                        con, mod_row["module_id"] if mod_row else "")
                except Exception:  # noqa: BLE001 -- no map, no probe
                    omap = {}
                try:
                    old_probe = card["last_probe"]
                except Exception:  # noqa: BLE001 -- pre-migration row
                    old_probe = None
                _, was_owned = omap.get(card["concept_id"], (0, False))
                now_iso = schedmod.iso(schedmod.utcnow())
                was_probe = bool(retestmod.probes_due(
                    [{"id": card_id, "card_id": card_id, "owned": was_owned,
                      "stability": card["stability"], "last_review": pre_review,
                      "last_probe": old_probe}], now_iso))
            except Exception:  # noqa: BLE001 -- probe check never blocks
                now_iso, was_probe = schedmod.iso(schedmod.utcnow()), False
            con.execute(
                "UPDATE cards SET stability=?, difficulty=?, retrievability=?, due=?,"
                " lapses=? WHERE id=?",
                (upd["stability"], upd["difficulty"], upd["retrievability"],
                 upd["due"], new_lapses, card_id))
            if was_probe:
                # Stamp after the INSERT so last_probe always covers the
                # just-recorded review (same-second equality counts).
                con.execute("UPDATE cards SET last_probe=? WHERE id=?",
                            (schedmod.iso(schedmod.utcnow()), card_id))
            # Batch 15, F-65: bank the confidence-weighted score with
            # the review — one calibration currency for reviews.
            try:
                points = confweightmod.score(result.get("pass"),
                                             int(confidence))
            except Exception:  # noqa: BLE001 -- banking must never raise
                points = 0
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence, submission,"
                " prev_stability, prev_difficulty, prev_retrievability,"
                " prev_due, prev_lapses, prev_mastery, points)"
                " VALUES(?,?,?,?,?,?,?,?,?,?,?)",
                (card_id, grade_val, int(confidence), str(submission)[:4000],
                 card["stability"], card["difficulty"], card["retrievability"],
                 card["due"], card["lapses"],
                 (prev_mastery["mastery"] or 0.0) if prev_mastery else 0.0,
                 points))
            # Roll concept mastery toward latest performance.
            con.execute(
                "UPDATE concepts SET mastery = mastery * 0.7 + ? * 0.3 WHERE id=?",
                (grade_val / 5.0, card["concept_id"]))
            # F-96: frustration relief — three fast fails on this card
            # route to an easier same-concept card plus a breather note.
            try:
                sibs = con.execute(
                    "SELECT id, difficulty FROM cards"
                    " WHERE concept_id=? AND id!=?",
                    (card["concept_id"], card_id)).fetchall()
                pool = [{"id": r["id"], "difficulty": r["difficulty"]}
                        for r in sibs]
                plan = frustcatchmod.relief_plan(hist + [grade_val],
                                                 pool, card_id)
            except Exception:  # noqa: BLE001 -- relief never blocks
                plan = {"frustrated": False, "streak": 0,
                        "easier": None, "message": ""}
            # F-99: two trailing fails split the concept into skill atoms
            # so reteach can target the failing part, not the whole card.
            try:
                rows = con.execute(
                    "SELECT grade, submission FROM reviews WHERE card_id=?"
                    " ORDER BY rowid DESC LIMIT 4",
                    (card_id,)).fetchall()
                attempts = [{"ok": r[0] >= 3, "note": r[1] or ""}
                            for r in reversed(rows)]
                concept = card["concept_id"]
                if skillatomsmod.needs_split(attempts):
                    atoms = skillatomsmod.decompose(concept, attempts)
                else:
                    atoms = []
                atoms_html = skillatomsmod.section_html(concept, atoms)
            except Exception:  # noqa: BLE001 -- atoms never block
                atoms_html = ""
            con.commit()
        finally:
            con.close()
        # Batch 15, F-66: settle the stated bet at explicit odds for
        # display. The banked currency stays score() (one account);
        # the drill line shows the fair-odds outcome beside it.
        try:
            deal = drillmod.offer(int(confidence))
            won = deal["win"] if result.get("pass") else deal["lose"]
            drill = (f"Drill: stated {int(deal['p'] * 100)}% — fair odds"
                     f" +{deal['win']}/{deal['lose']}, settled {won:+d}.")
        except Exception:  # noqa: BLE001 -- display must never raise
            drill = ""
        try:
            relief_html = ""
            if plan.get("frustrated"):
                lesson_url = ""
                if plan.get("easier") is not None and mod_row is not None:
                    # Anchor matches the lesson section id rendered by
                    # Handler.module_html (slug of the node, not the name).
                    node = card["concept_id"].split(":", 1)[1] \
                        if ":" in card["concept_id"] else card["concept_id"]
                    lesson_url = (
                        f"/modules/{mod_row['module_id']}"
                        f"#lesson-{lesmod.slug(node)}")
                relief_html = frustcatchmod.banner_html(plan, lesson_url)
        except Exception:  # noqa: BLE001 -- display must never raise
            relief_html = ""
        return {"result": result, "grade": grade_val, "next_due": upd["due"],
                "points": points, "drill": drill, "relief": relief_html,
                "atoms": atoms_html, "retry": retry_html}


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
