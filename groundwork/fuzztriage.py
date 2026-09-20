"""Fuzz-target triage: reproduce a crasher from a failing input (F-11, type 34).

The learner gets a function plus a fuzzer-found input that crashes it, and
must write the minimal reproducing call and/or name the crashing line.
Grading accepts either half: the exact crash call (whitespace-insensitive
substring match) or the crash line number. When a sandbox runner is passed,
the stored reference crash is re-run against the shown code to confirm the
crasher still reproduces (else the card is flagged stale); with
runner=None grading is a pure string/number match, so no harness is needed.

Plugin API: ``generate(ex_id, concept, snippet, ctx)``,
``render(exercise) -> html``, ``grade(exercise, submission, runner)``,
plus ``emits(ctx) -> bool`` (pipeline emission guard predicate).
Import-safe standalone: stdlib only (``ast``/``html``/``re``), no
groundwork imports. Registration lives in ``groundwork/exercises.py``
(TYPES, GENERATORS, BLOOM_TYPES); see ===WIRES===.

BLOOM bucket: analyse — the learner diagnoses which input crashes the
function and pinpoints where it breaks, like spot-bug (13) and
error-branch (28). Emission guard: fault-gated, skip when "buggy" not in
ctx — the crasher must be a verified-breaking mutation, since plain
runnable code passes its own harness and has no crash to reproduce.
"""
from __future__ import annotations

import ast
import html
import re

TYPE_NUM = 34
TYPE_NAME = "fuzz-triage"
BLOOM = "analyse"
AREA = "fuzztriage"


def _concept_field(concept, name: str, default: str = "") -> str:
    return str(getattr(concept, name, default) or default)


def _func_name(concept, code: str) -> str:
    """Def matching the concept, else the first def, else the concept name."""
    want = _concept_field(concept, "name", "func")
    try:
        tree = ast.parse(code)
    except (SyntaxError, ValueError):
        return want or "func"
    first = ""
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            if not first:
                first = node.name
            if node.name == want:
                return want
    return want if want else (first or "func")


def _code_for(concept, snippet: list[str], ctx: dict) -> str:
    code = str(ctx.get("buggy") or ctx.get("runnable")
              or "\n".join(snippet or []) or "").strip()
    if not code:
        name = _concept_field(concept, "name", "func")
        code = f"def {name}(x):\n    return x"
    return code


def _canon(call: str) -> str:
    return re.sub(r"\s+", "", str(call or ""))


def _ints(text: str) -> list[int]:
    return [int(tok) for tok in re.findall(r"-?\d+", str(text or ""))]


_CALL_ARGS_RE = re.compile(r"[A-Za-z_][A-Za-z0-9_]*\s*\([^()]*\)")


def _line_ints(text: str) -> list[int]:
    """Integers that read as line references, not call arguments.

    Digits inside a call's parentheses (``ratio(4, 2)``) are arguments,
    not line numbers — otherwise any wrong call containing the digit
    would pass. A bare number alone still counts as a line guess.
    """
    text = str(text or "")
    rest = _CALL_ARGS_RE.sub(" ", text)
    ints = _ints(rest)
    if ints:
        return ints
    if re.fullmatch(r"\s*-?\d+\s*", text):
        return _ints(text)
    return []


def _hints(fname: str, reported: str, file: str, line: int) -> list[str]:
    where = f"{file}:{line}" if file and line else (file or "the linked file")
    return [
        f"Run `{fname}` in your head on the reported input `{reported}` — find where it blows up.",
        f"Look at {where}: shrink the input to the smallest call that still crashes.",
        f"Worked step: reply with the crashing call plus its line number, e.g. `{reported} @ line {line or 'N'}`.",
    ]


def emits(ctx: dict | None) -> bool:
    """Emission guard predicate: only emit from a verified-breaking mutation."""
    return bool((ctx or {}).get("buggy"))


def generate(ex_id, concept, snippet, ctx) -> dict:
    """Build a fuzz-triage card: crashing function + failing input."""
    ctx = ctx or {}
    snippet = list(snippet or [])
    code = _code_for(concept, snippet, ctx)
    fname = _func_name(concept, code)
    try:
        crash_line = int(ctx.get("bug_line", 0) or 0)
    except (TypeError, ValueError):
        crash_line = 0
    crash_call = str(ctx.get("crash_call") or ctx.get("call")
                     or f"{fname}(...)").strip()
    reported = str(ctx.get("fuzz_input") or crash_call).strip()
    fault = str(ctx.get("fault") or ("the injected defect" if ctx.get("buggy")
                                     else "a crashing input"))
    grounded = bool(ctx.get("buggy"))
    if crash_line:
        back = f"`{crash_call}` crashes at line {crash_line} ({fault})."
    else:
        back = f"`{crash_call}` reproduces the crash ({fault})."
    front = (
        f"A fuzzer crashed `{fname}` with this input: `{reported}` "
        f"({fault}).\n"
        f"```python\n{code[:600]}\n```\n"
        f"Reply with the minimal reproducing call and the crashing line number."
    )
    name = _concept_field(concept, "name", fname)
    file = _concept_field(concept, "file")
    try:
        line = int(getattr(concept, "line", 0) or 0)
    except (TypeError, ValueError):
        line = 0
    return {
        "id": ex_id, "type": TYPE_NUM, "type_name": TYPE_NAME, "bloom": BLOOM,
        "concept_id": _concept_field(concept, "node_id", name),
        "concept": name,
        "file": file, "line": line,
        "commit": str(ctx.get("commit", "") or ""),
        "hints": _hints(fname, reported, file, line),
        "front": front, "back": back,
        "payload": {"code": code, "func": fname, "crash_call": crash_call,
                    "reported": reported, "crash_line": crash_line,
                    "fault": fault, "grounded": grounded},
    }


def _fail(msg: str) -> dict:
    return {"pass": False, "score": 0.0, "feedback": msg}


def grade(exercise: dict, submission: str, runner=None) -> dict:
    """Pass when the submission names the crash call or the crash line.

    Either half counts: the exact reproducing call (whitespace-insensitive)
    or the crashing line number. When ``runner`` is given, the stored
    reference crash is re-run against the shown code first — a reference
    that no longer crashes flags the card stale instead of passing anyone.
    Never raises: malformed inputs grade as fail, never throw.
    """
    try:
        payload = (exercise or {}).get("payload", {}) or {}
        code = str(payload.get("code", "") or "")
        crash_call = str(payload.get("crash_call", "") or "")
        try:
            crash_line = int(payload.get("crash_line", 0) or 0)
        except (TypeError, ValueError):
            crash_line = 0
        text = str(submission or "").strip()
        if not text:
            return _fail("Submit the minimal crashing call and its line number.")
        if runner is not None and code.strip() and crash_call.strip():
            try:
                ref = runner.run(code + f"\n{crash_call}\n")
                if getattr(ref, "ok", False):
                    return _fail("Crasher no longer reproduces; flagged stale.")
            except Exception:
                pass  # runner trouble must not fail a good repro
        want = _canon(crash_call)
        call_ok = bool(want) and want in _canon(text)
        line_ok = bool(crash_line) and crash_line in _line_ints(text)
        if call_ok and (not crash_line or line_ok):
            return {"pass": True, "score": 1.0,
                    "feedback": "Crasher reproduced at the right line."}
        if call_ok or line_ok:
            return {"pass": True, "score": 1.0,
                    "feedback": ("Repro call matches." if call_ok
                                 else f"Crash line {crash_line} identified.")}
        if crash_line:
            return _fail(f"Not the crasher — re-run `{payload.get('func', 'the function')}` "
                         f"on the reported input and name the failing line.")
        return _fail("Not the crasher — submit the exact failing call.")
    except Exception as exc:  # noqa: BLE001 — grading never raises
        return _fail(f"Could not grade this submission: {exc}")


def render(exercise: dict) -> str:
    """Exercise widget: prompt plus a call/line answer box."""
    payload = (exercise or {}).get("payload", {}) or {}
    front = html.escape(str(exercise.get("front", "")))
    concept = html.escape(str(exercise.get("concept", "")))
    type_name = html.escape(str(exercise.get("type_name", TYPE_NAME)))
    seed = html.escape(str(payload.get("reported", "")))
    file_line = f"{exercise.get('file', '')}:{exercise.get('line', 0)}"
    hints = "".join(
        f"<details><summary>Hint {i + 1}</summary>{html.escape(h)}</details>"
        for i, h in enumerate(exercise.get("hints", []))
    )
    return (
        f"<article><h3>{concept} · {type_name}</h3>"
        f"<p>{front}</p>"
        f"<details><summary>How grading works</summary>"
        f"<p><small>Name the exact crashing call or the crashing line — "
        f"either half counts.</small></p></details>"
        f"<form method='post'><textarea name='answer' rows='4' cols='70'>{seed}</textarea>"
        f"<br><button>Reproduce crash</button></form>{hints}"
        f"<p><small>{html.escape(file_line)}</small></p></article>"
    )


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        "<h3 id='status-b7-fuzztriage'>Fuzz-target triage <small>(feature)</small></h3>"
        "<p>Reproduce a fuzzer-found crash: write the minimal failing call "
        "and name the crashing line — either half counts. "
        "<code>groundwork/fuzztriage.py</code>.</p>"
    )
