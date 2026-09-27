"""Tailored timeout feedback: "infinite loop?" vs "too slow?" (I-183).

Learner code that overruns the sandbox wall clock fails today with a bare
``Output: ... timeout`` line, which never says whether the code is stuck
forever or merely slow. ``hint_text`` classifies the timeout from cheap
signals observable at grade time -- the measured stdout volume and shape
plus the learner's own submission text -- and returns one appended
feedback line, or "" when the evidence is ambiguous so the caller keeps
its legacy feedback byte-identical.

Verdicts from ``classify``: "loop" (runaway repeated output, or
``while True`` with no ``break``), "slow" (partial harness progress,
bounded loops only, or quiet self-recursive code), "unknown" (anything
else -- a diagnosis is never invented). Only timeouts of LEARNER code
may be classified; reference-run timeouts (predict/trace cards) stay
untouched. Stdlib only (``re``, ``html``, ``collections``); never raises.
"""
from __future__ import annotations

import html
import re
from collections import Counter

STATUS_ANCHOR = "status-b27-timefb"

LOOP_MIN_LINES = 20
LOOP_REPEAT_FRAC = 0.8
LOOP_MIN_BYTES = 4000

_PROGRESS_RE = re.compile(r"\b(pass(ed|es)?|ok)\b", re.IGNORECASE)
_DOTS_RE = re.compile(r"^[.\d\s/]+$")
_UNBOUNDED_RE = re.compile(
    r"^\s*while\s+(True|1)\s*:|^\s*while\s*\(\s*true\s*\)", re.MULTILINE)
_BREAK_RE = re.compile(r"^\s*break\b", re.MULTILINE)
_FOR_RE = re.compile(r"^\s*for\b", re.MULTILINE)
_WHILE_RE = re.compile(r"^\s*while\b", re.MULTILINE)
_DEF_RE = re.compile(r"(?m)^\s*def\s+(\w+)\s*\(")
_NEXT_DEF_RE = re.compile(r"(?m)^(?:def|class)\s+\w+")


def _text(value) -> str:
    """Best-effort text; "" for missing/hostile input. Never raises."""
    try:
        if value is None:
            return ""
        if isinstance(value, bytes):
            return value.decode("utf-8", "replace")
        if isinstance(value, str):
            return value
        return str(value)
    except Exception:  # noqa: BLE001 -- coercion never raises
        return ""


def _field(res, name: str):
    """RunResult attr or dict key; "" when unreadable. Never raises."""
    try:
        if isinstance(res, dict):
            return res.get(name, "")
        return getattr(res, name, "")
    except Exception:  # noqa: BLE001 -- probing never raises
        return ""


def is_timeout(res) -> bool:
    """True only for a FAILED run stamped timeout. Never raises."""
    try:
        if _field(res, "ok"):
            return False
        err = _text(_field(res, "stderr")).lower()
        return "timeout" in err or "timed out" in err
    except Exception:  # noqa: BLE001 -- probing never raises
        return False


def _repetition(stdout: str) -> tuple:
    """(line_count, top_line_share, top_line) of measured stdout."""
    lines = [line for line in stdout.splitlines() if line.strip()]
    if not lines:
        return (0, 0.0, "")
    top, count = Counter(lines).most_common(1)[0]
    return (len(lines), count / len(lines), top[:80])


def _progressed(stdout: str) -> bool:
    """True when partial stdout shows harness progress (PASS/ok/dots)."""
    for line in stdout.splitlines():
        text = line.strip()
        if not text:
            continue
        if _PROGRESS_RE.search(text):
            return True
        if len(text) >= 4 and _DOTS_RE.match(text):
            return True
    return False


def _recursive(sub: str) -> bool:
    """True when a defined function calls itself in its own body."""
    for match in _DEF_RE.finditer(sub):
        name = match.group(1)
        rest = sub[match.end():]
        nxt = _NEXT_DEF_RE.search(rest)
        body = rest[:nxt.start()] if nxt else rest
        if re.search(r"\b%s\s*\(" % re.escape(name), body):
            return True
    return False


def _signals(res, submission) -> dict:
    """All measured signals plus the verdict. Never raises."""
    try:
        out = _text(_field(res, "stdout"))
        sub = _text(submission)
        lines, frac, top = _repetition(out)
        repeat_hit = lines >= LOOP_MIN_LINES and frac >= LOOP_REPEAT_FRAC
        volume_hit = len(out) >= LOOP_MIN_BYTES
        progressed = _progressed(out)
        unbounded = (bool(_UNBOUNDED_RE.search(sub))
                     and not _BREAK_RE.search(sub))
        has_while = bool(_WHILE_RE.search(sub))
        has_for = bool(_FOR_RE.search(sub))
        recursive = _recursive(sub) if sub.strip() else False
        if not is_timeout(res) or not sub.strip():
            verdict = "unknown"
        elif repeat_hit:
            verdict = "loop"
        elif progressed:
            verdict = "slow"
        elif volume_hit:
            verdict = "loop"
        elif unbounded:
            verdict = "loop"
        elif recursive or not has_while:
            verdict = "slow"
        else:
            verdict = "unknown"  # e.g. while-with-break: ambiguous
        return {"verdict": verdict, "lines": lines, "frac": frac,
                "top": top, "bytes": len(out), "repeat_hit": repeat_hit,
                "volume_hit": volume_hit, "progressed": progressed,
                "unbounded": unbounded, "has_for": has_for,
                "has_while": has_while, "recursive": recursive,
                "sub": sub}
    except Exception:  # noqa: BLE001 -- signals never raise
        return {"verdict": "unknown", "lines": 0, "frac": 0.0, "top": "",
                "bytes": 0, "repeat_hit": False, "volume_hit": False,
                "progressed": False, "unbounded": False, "has_for": False,
                "has_while": False, "recursive": False, "sub": ""}


def classify(res, submission) -> str:
    """Timeout verdict: "loop", "slow", or "unknown". Never raises."""
    return _signals(res, submission)["verdict"]


def hint_text(res, submission) -> str:
    """One appended feedback line, or "" to keep legacy byte-identical."""
    sig = _signals(res, submission)
    if sig["verdict"] == "loop":
        if sig["repeat_hit"]:
            return (
                f"Timed out after printing {sig['lines']} lines -- mostly "
                f"{sig['top']!r} repeated. That pattern usually means an "
                "infinite loop: find the loop doing the printing and check "
                "when it stops.")
        if sig["volume_hit"]:
            return (
                f"Timed out after printing {sig['bytes']} bytes with no "
                "test progress -- usually a runaway loop. Check what each "
                "loop prints and when it stops.")
        return ("Timed out -- your `while True` has no `break`, so it may "
                "never exit. Add an exit condition or a `break` on the "
                "done path.")
    if sig["verdict"] == "slow":
        if sig["progressed"]:
            base = ("Timed out, but the run made partial progress before "
                    "the cutoff -- your code advances, it is just too slow "
                    "for the time limit. Cut work the hot loop repeats.")
        elif sig["has_for"] and not sig["has_while"]:
            base = ("Timed out with no sign of a runaway loop -- likely "
                    "just too slow for the time limit. Shrink the ranges "
                    "your `for` loops cover, or memoize calls they repeat.")
        else:
            base = ("Timed out with no sign of a runaway loop -- likely "
                    "just too slow for the time limit. Look for work the "
                    "hot path repeats: big ranges, nested loops, or "
                    "exponential recursion.")
        if "input(" in sig["sub"]:
            base += (" Also note the sandbox has no keyboard: a bare "
                     "`input()` waits forever and always times out.")
        return base
    return ""


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "timeout-loop-or-slow",
        "kind": "improvement",
        "title": "Timeout feedback: loop or slow?",
        "blurb": "Timed-out code says whether it looks stuck in a loop or just slow -- from measured output, never guessed.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }


def section_html() -> str:
    """Anchored status subsection; joined by the batch27 home module."""
    try:
        loop = hint_text(
            {"ok": False, "stdout": "x\n" * 30, "stderr": "timeout"},
            "while True:\n    print('x')")
        slow = hint_text(
            {"ok": False, "stdout": "PASS t1\nPASS t2\n", "stderr": "timeout"},
            "def f(n):\n    return sum(range(n))")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Timeout feedback: loop or slow? "
            "<small>(improvement)</small></h3>"
            "<p>Timed-out learner code used to fail with a bare "
            "<code>timeout</code> line. <code>groundwork/timefb.py</code> "
            "reads the timed-out run's measured output (volume, repetition, "
            "partial progress) plus the submission's loop shapes at grade "
            "time (<code>exercises.grade</code>) and appends one line -- an "
            "infinite-loop nudge or a too-slow nudge -- staying silent when "
            "the evidence is ambiguous so legacy feedback is byte-identical. "
            "Live samples below.</p>"
            f"<p><code>loop:</code> {html.escape(loop)}</p>"
            f"<p><code>slow:</code> {html.escape(slow)}</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Timeout feedback</h3>"
                "<p>Timeout help temporarily unavailable.</p>")
