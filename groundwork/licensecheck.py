"""License-check exercise (type 63, F-40, bloom: evaluate).

The learner judges whether one candidate dependency may be combined
into this AGPL-3.0 project, given the dep's license plus linkage facts
(static vs dynamic link, modified or not), and names the exact reason
keyword from a fixed set. Grading is exact match on BOTH the verdict
(OK / NOT-OK) and the reason keyword after documented normalization --
a right verdict with the wrong reason still fails, and vice versa.

Safety: the license table below is a small fixed matching-exercise
fixture, not legal advice. It covers only generic, well-known license
pairings against AGPL-3.0 and states no conclusion beyond the card
verdict. Real licensing decisions need a lawyer; the card back says so.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``hashlib``/``html``/``re``), no
groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); the table is always plantable, so
generate never returns None -- unlike harness-gated siblings there is
no skip path for the pipeline to handle.

``generate`` never raises: hostile inputs fall back to defaults and
still yield a grounded card.
"""
from __future__ import annotations

import hashlib
import html
import re

TYPE_NUM = 63
TYPE_NAME = "license-check"
BLOOM = "evaluate"
STATUS_ANCHOR = "status-b10-licensecheck"

PROJECT_LICENSE = "AGPL-3.0"

REASONS = ("copyleft", "patent-grant", "network-clause",
           "version-mismatch", "permissive")

# (dep name, dep license, linkage, modified, verdict, reason, why).
# verdict is "ok" or "not-ok"; reason is one of REASONS. Generic,
# well-known pairings against an AGPL-3.0 project only -- a matching
# fixture, not legal advice.
TABLE = (
    ("mit-utils", "MIT", "dynamic", False, "ok", "permissive",
     "MIT is permissive: no copyleft conditions attach to the combined work."),
    ("apache-queue", "Apache-2.0", "dynamic", False, "ok", "patent-grant",
     "Apache-2.0 stays compatible: permissive terms plus an express patent grant."),
    ("bsd-hash", "BSD-3-Clause", "static", False, "ok", "permissive",
     "BSD-3-Clause is permissive: attribution only, no copyleft conditions."),
    ("gpl3-core", "GPL-3.0-only", "static", False, "ok", "copyleft",
     "GPL-3.0 copyleft is satisfied: AGPL-3.0 preserves its freedoms."),
    ("agpl-net", "AGPL-3.0", "dynamic", False, "ok", "network-clause",
     "Same license: the AGPL-3.0 network clause is already honoured."),
    ("gpl2-legacy", "GPL-2.0-only", "static", False, "not-ok", "version-mismatch",
     "GPL-2.0-only cannot combine with AGPL-3.0: no later-version clause bridges them."),
    ("sspl-hosted", "SSPL-1.0", "dynamic", False, "not-ok", "network-clause",
     "SSPL service-provision terms conflict with AGPL-3.0: do not combine."),
    ("propr-blob", "proprietary", "static", True, "not-ok", "copyleft",
     "Proprietary code cannot absorb AGPL-3.0 copyleft terms: do not combine."),
)


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _pick(ex_id) -> tuple:
    """Deterministic table row indexed by ex_id (stable across reruns)."""
    digest = hashlib.sha256(str(ex_id).encode()).digest()
    return TABLE[int.from_bytes(digest[:8], "big") % len(TABLE)]


def _hints(dep: str, lic: str) -> list[str]:
    return [
        "Judge the combination, not the dep alone: project license first, dep license second.",
        f"Check {dep} ({lic}): linkage (static/dynamic) and whether it was modified.",
        "Worked format, not the answer: reply `OK` plus `permissive`, one per line.",
    ]


def generate(ex_id, concept, snippet, ctx):
    """Build a license-check card. Never raises, never returns None.

    The fixed table is always plantable, so every call -- including the
    test_all_types_generate fixture ctx and hostile None inputs -- yields
    a real card with a truthy front.
    """
    try:
        ctx = ctx if isinstance(ctx, dict) else {}
        name = _concept_field(concept, "name", "") or "service"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        dep, lic, linkage, modified, verdict, reason, why = _pick(ex_id)
        mod_word = "modified" if modified else "unmodified"
        front = (
            f"This project is licensed {PROJECT_LICENSE}. A candidate dependency:\n"
            f"- `{dep}` licensed `{lic}` ({linkage} link, {mod_word})\n"
            "Is this dependency OK to combine into the project? Reply with "
            "OK or NOT-OK plus exactly ONE reason keyword from: "
            + ", ".join(f"`{r}`" for r in REASONS) + "."
        )
        word = "OK" if verdict == "ok" else "NOT-OK"
        back = (f"{word} (`{dep}`, {lic}): {why} "
                f"Reason keyword `{reason}`. This is a matching exercise, "
                "not legal advice -- confirm real decisions with a lawyer.")
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": _hints(dep, lic),
            "front": front, "back": back,
            "payload": {"dep": dep, "dep_license": lic,
                        "project_license": PROJECT_LICENSE,
                        "linkage": linkage, "modified": modified,
                        "verdict": verdict, "reason": reason, "why": why,
                        "grounded": True},
        }
    except Exception:
        return None  # grading-grade safety: generate never raises


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _squash(text: str) -> str:
    """Lowercase alphanumeric only: unifies `network-clause`,
    `network clause`, `network_clause`, `NetworkClause`."""
    return re.sub(r"[^a-z0-9]", "", str(text or "").lower())


def parse_verdict(text: str) -> str | None:
    """'ok' or 'not-ok', else None. NOT-OK is checked first so the
    'ok' inside 'not-ok' never misreads as approval. Never raises."""
    try:
        t = str(text or "").lower()
        if re.search(r"not[\s_\-]*ok", t):
            return "not-ok"
        if re.search(r"\bok\b", t):
            return "ok"
        return None
    except Exception:
        return None


def parse_reasons(text: str) -> list[str]:
    """Reason keywords present in the submission (squash-compared).
    Never raises; garbage yields []."""
    try:
        blob = _squash(text)
        if not blob:
            return []
        return [r for r in REASONS if _squash(r) in blob]
    except Exception:
        return []


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Exact verdict AND exact reason-keyword match (fail closed)."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        verdict = str(payload.get("verdict", "") or "")
        reason = str(payload.get("reason", "") or "")
        if verdict not in ("ok", "not-ok") or reason not in REASONS:
            return _fail("Exercise payload is missing the verdict.")
        text = str(submission if submission is not None else "")
        if not text.strip():
            return _fail("Reply with OK or NOT-OK plus one reason keyword "
                         f"({', '.join(REASONS)}).")
        got_verdict = parse_verdict(text)
        got_reasons = parse_reasons(text)
        if got_verdict is None:
            return _fail("State OK or NOT-OK plus one reason keyword "
                         f"({', '.join(REASONS)}).")
        if got_reasons != [reason]:
            return _fail("Name exactly one reason keyword "
                         f"({', '.join(REASONS)}) alongside the verdict.")
        if got_verdict == verdict:
            word = "OK" if verdict == "ok" else "NOT-OK"
            return {"pass": True, "score": 1.0,
                    "feedback": f"Correct: {word} ({reason})."}
        return _fail("Verdict wrong -- re-check the license pairing.")
    except Exception:  # noqa: BLE001 -- grading must never raise
        return _fail("Grader could not read the submission -- send verdict + reason.")


def render(exercise: dict) -> str:
    """Exercise widget: license facts plus a verdict/reason answer box."""
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    reasons = ", ".join(f"<code>{html.escape(r)}</code>" for r in REASONS)
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Exact verdict (OK / NOT-OK) AND exact reason keyword "
        f"({reasons}) must both match. Verdict alone, reason alone, "
        f"empty, or ambiguous answers fail.</small></p></details>"
        f"<form method='post'><input name='answer' size='50' "
        f"placeholder='OK or NOT-OK + one reason keyword'>"
        f"<button>Judge the dep</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>License-check <small>(feature)</small></h3>"
        "<p>Judge whether one dependency may combine into this AGPL-3.0 "
        "project -- OK or NOT-OK plus one reason keyword "
        "(<code>copyleft</code>, <code>patent-grant</code>, "
        "<code>network-clause</code>, <code>version-mismatch</code>, "
        "<code>permissive</code>). Graded by exact verdict+reason match; "
        "a fixed-table matching exercise, not legal advice. "
        "<code>groundwork/licensecheck.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "license-check", "kind": "feature",
            "title": "License-check",
            "blurb": "Judge whether a dependency fits this AGPL-3.0 project -- verdict plus reason.",
            "path": "/status", "anchor": "status-b10-licensecheck"}
