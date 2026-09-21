"""Regex authoring exercise (type 54, F-31, bloom: apply).

The learner writes a regular expression that must match all required
positive cases and reject all negative cases; grading runs the fixed
case-suite stored in the card payload as pure ``re`` fullmatches.
No sandbox runner is needed (pure-re grading, like the proptest and
docdoctest siblings).

The suite is data, independent of the snippet: match shapes are fixed
literal families (order id / ISO date / token) picked deterministically
from the exercise id, so generation never invents expected outputs and
grading is reproducible. The card also stores a reference solution that
is verified against the suite at generation time (measured with ``re``,
never invented). Emission needs no harness/mutation guard: grading is
pure ``re`` over the stored suite, so the card emits on every concept.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``.
Import-safe standalone: stdlib only (``hashlib``/``html``/``re``),
no groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); pipeline needs no skip guard.
"""
from __future__ import annotations

import hashlib
import html
import re

TYPE_NUM = 54
TYPE_NAME = "regex-authoring"
BLOOM = "apply"
STATUS_ANCHOR = "status-b9-regexex"

MAX_CASES = 12
MAX_CASE_LEN = 64
MAX_PATTERN_LEN = 200


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


_FAMILIES = (
    {
        "shape": "order id like `ORD-0001` (prefix `ORD-` plus exactly 4 digits)",
        "reference": r"ORD-[0-9]{4}",
        "positives": ["ORD-0001", "ORD-8364", "ORD-1234", "ORD-9999"],
        "negatives": ["ORD-123", "ORD-12345", "ord-1234", "ORD-12AB",
                      " ORD-1234"],
    },
    {
        "shape": "ISO date like `2026-09-21` "
                 "(4 digits, dash, 2 digits, dash, 2 digits)",
        "reference": r"[0-9]{4}-[0-9]{2}-[0-9]{2}",
        "positives": ["2026-09-21", "1999-01-01", "2024-02-29",
                      "2000-12-31"],
        "negatives": ["2026-9-21", "2026/09/21", "21-09-2026",
                      "2026-09-21 ", "Sept 21"],
    },
    {
        "shape": "token like `tok_a1b2c3d4` "
                 "(prefix `tok_` plus exactly 8 lowercase letters/digits)",
        "reference": r"tok_[a-z0-9]{8}",
        "positives": ["tok_a1b2c3d4", "tok_00000000", "tok_zzzz9999",
                      "tok_q7w8e9r0"],
        "negatives": ["tok_A1B2C3D4", "tok_a1b2c3", "tok_a1b2c3d4e",
                      "TOK_a1b2c3d4", "tok_a1b2 c3d4"],
    },
)


def _family(ex_id: str) -> dict:
    digest = hashlib.sha256(str(ex_id).encode()).hexdigest()
    return _FAMILIES[int(digest, 16) % len(_FAMILIES)]


def _suite_ok(fam: dict) -> bool:
    """True when the family reference goes green on its own suite."""
    try:
        rx = re.compile(fam["reference"])
        return (all(rx.fullmatch(s) for s in fam["positives"])
                and not any(rx.fullmatch(s) for s in fam["negatives"]))
    except re.error:
        return False


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a regex-authoring card; never raises."""
    try:
        ctx = ctx or {}
        name = _concept_field(concept, "name", "service") or "service"
        file = _concept_field(concept, "file")
        try:
            line = int(getattr(concept, "line", 0) or 0)
        except (TypeError, ValueError):
            line = 0
        commit = str(ctx.get("commit", "") or "")
        fam = _family(ex_id)
        if not _suite_ok(fam):
            fam = _FAMILIES[0]
        positives = list(fam["positives"])[:MAX_CASES]
        negatives = list(fam["negatives"])[:MAX_CASES]
        must = "\n".join(f"  + `{s}`" for s in positives)
        must_not = "\n".join(f"  - `{s}`" for s in negatives)
        front = (
            f"Write a regular expression (Python `re` syntax) for `{name}` "
            f"that matches exactly this shape: {fam['shape']}.\n"
            f"Must match:\n{must}\nMust reject:\n{must_not}\n"
            "Reply with the pattern alone — bare, no `/slashes/`, no flags.")
        back = (f"{fam['reference']}  (model answer — any pattern going "
                "green on every case above counts).")
        hints = [
            "Anchor on the literal parts first (`ORD-`, dashes, `tok_`), "
            "then pin each slot with a character class plus an exact count.",
            "Reject-cases fail on near-misses: check lengths (`{4}` not `+`), "
            "case (`[0-9]` rejects letters), and stray spaces.",
            f"Worked step: `{fam['reference']}` goes green on all "
            f"{len(positives) + len(negatives)} cases — read why, then "
            "write your own.",
        ]
        return {
            "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
            "bloom": BLOOM,
            "concept_id": _concept_field(concept, "node_id", name),
            "concept": name, "file": file, "line": line, "commit": commit,
            "hints": hints, "front": front, "back": back,
            "payload": {"shape": fam["shape"],
                        "reference": fam["reference"],
                        "positives": positives, "negatives": negatives,
                        "grounded": True},
        }
    except Exception:  # never raise on the generic suite ctx
        fam = _FAMILIES[0]
        return {"id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME,
                "bloom": BLOOM, "concept_id": "service",
                "concept": "service", "file": "", "line": 0, "commit": "",
                "hints": ["Pin the literals.", "Pin the counts.",
                          "Reject the near-misses."],
                "front": f"Write a regex matching {fam['shape']}.",
                "back": fam["reference"],
                "payload": {"shape": fam["shape"],
                            "reference": fam["reference"],
                            "positives": list(fam["positives"]),
                            "negatives": list(fam["negatives"]),
                            "grounded": True}}


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def _strip_pattern(text: str) -> str:
    t = str(text).strip()
    if len(t) >= 2 and t.startswith("/") and t.rfind("/") > 0:
        t = t[1:t.rfind("/")]  # tolerate /.../ delimiters
    return t.strip()


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Fullmatch the submission over every stored case. Never raises."""
    _ = runner
    try:
        payload = (exercise or {}).get("payload", {})
        positives = list(payload.get("positives", []) or [])[:MAX_CASES]
        negatives = list(payload.get("negatives", []) or [])[:MAX_CASES]
        if not positives or not negatives:
            return _fail("Exercise payload is missing the case suite.")
        pattern = _strip_pattern(submission
                                 if submission is not None else "")
        if not pattern:
            return _fail("Submit a regular expression pattern "
                         "(bare, no slashes needed).")
        if len(pattern) > MAX_PATTERN_LEN:
            return _fail(f"Pattern too long ({len(pattern)}>"
                         f"{MAX_PATTERN_LEN} chars) — keep it simple.")
        try:
            rx = re.compile(pattern)
        except re.error as exc:
            return _fail(f"Pattern does not compile: {exc}.")
        cases = [("match", s) for s in positives]
        cases += [("reject", s) for s in negatives]
        misses: list[tuple[str, str]] = []
        for want, s in cases:
            s = str(s)
            if len(s) > MAX_CASE_LEN:
                misses.append((want, s))  # hostile case fails closed
                continue
            try:
                hit = rx.fullmatch(s) is not None
            except Exception:  # noqa: BLE001 — a bad match is a grade
                hit = False
            if (want == "match") != hit:
                misses.append((want, s))
        total = len(cases)
        score = (total - len(misses)) / max(1, total)
        if not misses:
            return {"pass": True, "score": 1.0,
                    "feedback": f"All {total}/{total} cases green."}
        want, s = misses[0]
        verb = ("should match but did not" if want == "match"
                else "should be rejected but matched")
        return {"pass": False, "score": score,
                "feedback": f"{total - len(misses)}/{total} cases green. "
                            f"First miss: {s[:40]!r} {verb} — "
                            "tighten or widen the pattern."}
    except Exception:  # noqa: BLE001 — grading must never raise
        return _fail("Grader could not read the submission — "
                     "submit a regex pattern.")


def render(exercise: dict) -> str:
    """Exercise widget: case lists plus a pattern textarea."""
    payload = (exercise or {}).get("payload", {})
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", [])))
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Your pattern is fullmatched against every listed case; "
        f"every case must go green to pass (partial credit per case), "
        f"no sandbox.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='3' cols='70' "
        f"placeholder='e.g. ORD-[0-9]{{4}}'></textarea>"
        f"<br><button>Check pattern</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>")


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Regex authoring <small>(feature)</small></h3>"
        "<p>Write a regular expression that matches every required case "
        "and rejects every negative case — graded by fullmatching the "
        "stored case-suite with pure <code>re</code>, no sandbox. "
        "<code>groundwork/regexex.py</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "regex-authoring", "kind": "feature",
            "title": "Regex authoring",
            "blurb": "Write a regex that matches every required case and rejects the rest — graded on a fixed case-suite.",
            "path": "/status", "anchor": "status-b9-regexex"}
