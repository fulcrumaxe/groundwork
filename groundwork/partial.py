"""Per-blank partial-credit display for multi-blank cloze (I-160).

The type-2 cloze grader in exercises.grade already scores per blank
but its feedback names only the wrong ids ("Blank(s) [1] wrong") —
a learner who gets 2 of 3 right sees nothing about what passed.
This module is the display side only: pure functions that turn the
cloze payload plus the keyed submission into a per-blank checklist.

Called from MCPServer.submit_review (the Due-queue POST
/cards/<id>/review learner path): the plain-text ``summary_line``
rides on the grade feedback, and ``checklist_html`` is available
for richer screens. Never grades, never stores.
No-data fallback: empty payload or empty submission parses to []
and checklist_html([]) is "", so legacy cards render unchanged.

Matching mirrors exercises.grade exactly (whitespace-folded string
equality, then AST-dump equality for code); local copies keep this
module dependency-free and under the area cap.
"""
from __future__ import annotations

import ast
import html

STATUS_ANCHOR = "status-b24-partial"


def _norm(code: str) -> str:
    return " ".join(str(code).strip().split())


def _ast_norm(code: str) -> str | None:
    try:
        return ast.dump(ast.parse(str(code)))
    except (SyntaxError, ValueError):
        return None


def _parse_keyed(submission: str) -> dict:
    """Parse `id=value` lines (one per line) into {id: value}."""
    out: dict = {}
    for line in str(submission).splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            k = k.strip()
            try:
                out[int(k)] = v.strip()
            except ValueError:
                out[k] = v.strip()
    return out


def _blank_match(answers: list, given: str) -> bool:
    """Same two-step match as the type-2 grader: norm, then AST."""
    want = [_norm(a) for a in answers]
    if _norm(given) in want:
        return True
    an = _ast_norm(given)
    return any(an is not None and an == _ast_norm(a) for a in answers)


def per_blank(payload: dict, submission: str) -> list[dict]:
    """One {id, passed, given, answers} record per blank, payload order.

    Never raises: non-dict payloads or unparsable submissions yield []
    (legacy no-data fallback). Single-blank cards accept the bare
    answer, mirroring the grader.
    """
    if not isinstance(payload, dict):
        return []
    blanks = payload.get("blanks")
    if not blanks:
        single = payload.get("answers")
        if not single:
            return []
        blanks = [{"id": 0, "answers": single}]
    try:
        given = _parse_keyed(submission)
    except Exception:  # noqa: BLE001 -- display never breaks review
        return []
    if not given and len(blanks) == 1:
        try:
            given = {blanks[0].get("id", 0): str(submission).strip()}
        except Exception:  # noqa: BLE001
            return []
    rows = []
    for b in blanks:
        try:
            bid = b.get("id", 0)
            answers = b.get("answers", []) or [""]
            val = given.get(bid, given.get(str(bid), ""))
            rows.append({"id": bid, "passed": bool(_blank_match(answers, val)),
                         "given": val, "answers": list(answers)})
        except Exception:  # noqa: BLE001 -- skip malformed blanks
            continue
    return rows


def summary_line(rows: list[dict]) -> str:
    """One-line verdict, e.g. '2 of 3 blanks right — blank 1 to retry'."""
    if not rows:
        return "No blank data — graded as before."
    ok = [r for r in rows if r.get("passed")]
    missed = [str(r.get("id")) for r in rows if not r.get("passed")]
    if not missed:
        return f"All {len(rows)} blank{'s' if len(rows) != 1 else ''} right."
    return (f"{len(ok)} of {len(rows)} blanks right — "
            f"blank{'' if len(missed) == 1 else 's'} "
            f"{', '.join(missed)} to retry.")


def checklist_html(rows: list[dict]) -> str:
    """Escaped <ul> checklist: ✓ per passed blank, ✗ + answer per miss.

    Returns "" for empty input so callers append unconditionally and
    legacy cards render byte-identical.
    """
    if not rows:
        return ""
    try:
        items = []
        for r in rows:
            bid = html.escape(str(r.get("id")))
            if r.get("passed"):
                items.append(f"<li>✓ Blank {bid} — "
                             f"<code>{html.escape(str(r.get('given', ''))[:60])}</code></li>")
            else:
                want = html.escape(str((r.get("answers") or [''])[0])[:60])
                items.append(f"<li>✗ Blank {bid} — expected <code>{want}</code></li>")
        return ("<ul class='partial-checklist'>" + "".join(items) + "</ul>")
    except Exception:  # noqa: BLE001 -- display must never raise
        return ""


def section_html() -> str:
    """Status-page demo: fixed fixture, no DB, never web.py."""
    rows = per_blank({"blanks": [{"id": 0, "answers": ["timeout"]},
                                 {"id": 1, "answers": ["retries"]}]},
                     "0=timeout\n1=wrng")
    return (f"<h3 id='{STATUS_ANCHOR}'>Per-blank partial credit "
            f"<small>(improvement)</small></h3>"
            f"<p>{html.escape(summary_line(rows))} "
            f"<code>groundwork/partial.py</code>.</p>{checklist_html(rows)}")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "partial-credit-blanks",
        "kind": "improvement",
        "title": "Per-blank partial credit",
        "blurb": "Miss a multi-blank cloze and the result names which blanks passed — retry the miss, not the whole card.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
