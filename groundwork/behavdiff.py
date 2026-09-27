"""Refactor behavior-diff (I-172): measured output equivalence on samples.

Refactor-under-test cards (``exercises.grade`` type 19) pass today with
a bare "Tests pass." that never shows the two versions agreeing. This
module closes that gap: it takes the sample call(s) straight from the
stored assert-only harness (``pipeline.build_ctx`` writes
``_out = repr(<call>)``), re-runs BOTH the reference and the learner
submission on each call through the existing sandbox runner, and
renders the measured outputs side by side -- proof of equivalence, not
a guess. Nothing is invented: every output shown was just measured,
and anything unmeasurable renders as "" so the grade caller keeps its
legacy feedback byte-identical. No sandbox changes (the runner is only
called, never modified), no schema changes, stdlib only; never raises.
"""
from __future__ import annotations

import ast
import html
import re

STATUS_ANCHOR = "status-b26-behavdiff"

MAX_SAMPLES = 4
MAX_CALL = 200
MAX_OUT = 300

_HARNESS_PREFIX = re.compile(r"^\s*(_out\s*=|print\s*\()")


def _repr_inner(line) -> str:
    """Text inside the first repr(...) call; "" when none/unbalanced."""
    try:
        if not isinstance(line, str):
            return ""
        i = line.find("repr(")
        if i < 0:
            return ""
        j = i + len("repr(")
        depth = 1
        quote = ""
        k = j
        while k < len(line):
            ch = line[k]
            if quote:
                if ch == "\\":
                    k += 2
                    continue
                if ch == quote:
                    quote = ""
            elif ch in ("'", '"'):
                quote = ch
            elif ch == "(":
                depth += 1
            elif ch == ")":
                depth -= 1
                if depth == 0:
                    return line[j:k]
            k += 1
        return ""
    except Exception:  # noqa: BLE001 -- parsing never raises
        return ""


def sample_calls(tests, cap: int = MAX_SAMPLES) -> list:
    """Sample call exprs from harness eval lines; [] when none/hostile.

    Only ``_out = ...`` and ``print(...)`` lines are read, so the
    ``assert _out == '<expected>'`` literal can never leak in as a fake
    sample. Each candidate must parse as an expression. Never raises.
    """
    try:
        try:
            n = int(cap)
        except (TypeError, ValueError):
            n = MAX_SAMPLES
        if not isinstance(tests, str) or not tests.strip():
            return []
        out = []
        for line in tests.splitlines():
            if len(out) >= max(0, n):
                break
            if not _HARNESS_PREFIX.match(line):
                continue
            inner = _repr_inner(line).strip()
            if not inner or len(inner) > MAX_CALL or inner in out:
                continue
            try:
                ast.parse(inner, mode="eval")
            except (SyntaxError, ValueError):
                continue
            out.append(inner)
        return out
    except Exception:  # noqa: BLE001
        return []


def measure(runner, code, call):
    """Measured stdout of code+call via runner; None when unmeasurable.

    Runs ``code`` plus a trailing ``print(repr(<call>))`` probe and
    returns the probe's (last) output line. Never raises.
    """
    try:
        if runner is None or not hasattr(runner, "run"):
            return None
        if not isinstance(code, str) or not code.strip():
            return None
        if not isinstance(call, str) or not call.strip():
            return None
        res = runner.run(code + "\nprint(repr(" + call.strip() + "))")
        if res is None or not getattr(res, "ok", False):
            return None
        text = getattr(res, "stdout", "") or ""
        lines = str(text).strip().splitlines()
        if not lines:
            return None
        return lines[-1].strip()
    except Exception:  # noqa: BLE001 -- measuring never raises
        return None


def sample_rows(reference, submission, tests, runner,
                cap: int = MAX_SAMPLES) -> list:
    """One measured row per sample call; [] when nothing measurable.

    Row: {"call", "ref", "sub", "match"}. A call is skipped unless BOTH
    sides measure. Never raises.
    """
    try:
        rows = []
        for call in sample_calls(tests, cap):
            ref = measure(runner, reference, call)
            sub = measure(runner, submission, call)
            if ref is None or sub is None:
                continue
            rows.append({"call": call, "ref": ref, "sub": sub,
                         "match": ref == sub})
        return rows
    except Exception:  # noqa: BLE001
        return []


def _short(text, cap: int = MAX_OUT) -> str:
    try:
        s = str(text)
    except Exception:  # noqa: BLE001
        return ""
    if len(s) > cap:
        return s[:cap] + "..."
    return s


def grade_extra(payload, submission, runner, cap: int = MAX_SAMPLES) -> str:
    """Plain-text behavior-diff for the type-19 grade feedback.

    "" when nothing is measurable (missing tests/reference, failing
    probes, hostile input), so the caller keeps legacy bytes. On full
    agreement every measured output is shown as proof; on divergence
    each differing sample pairs reference vs yours. Never raises.
    """
    try:
        if not isinstance(payload, dict):
            return ""
        reference = payload.get("reference") or payload.get("original") or ""
        tests = payload.get("tests") or ""
        if not isinstance(reference, str) or not isinstance(tests, str):
            return ""
        rows = sample_rows(reference, submission, tests, runner, cap)
        if not rows:
            return ""
        bad = [r for r in rows if not r["match"]]
        if not bad:
            head = (f"Behavior matches on {len(rows)} sample "
                    f"input{'s' if len(rows) != 1 else ''} (measured):")
            lines = [head] + [f"  [x] {r['call']} -> {_short(r['ref'])}"
                              for r in rows]
            return "\n".join(lines)
        head = (f"Behavior differs on {len(bad)} of {len(rows)} sample "
                f"input{'s' if len(rows) != 1 else ''} (measured):")
        lines = [head] + [
            f"  [ ] {r['call']}: reference {_short(r['ref'])} "
            f"vs yours {_short(r['sub'])}" for r in bad]
        return "\n".join(lines)
    except Exception:  # noqa: BLE001 -- feedback never raises
        return ""


def rows_html(rows) -> str:
    """Side-by-side HTML table over measured rows; "" when empty/hostile."""
    try:
        if not isinstance(rows, list) or not rows:
            return ""
        body = []
        for r in rows:
            if not isinstance(r, dict):
                continue
            call = html.escape(str(r.get("call", "")))
            ref = html.escape(_short(r.get("ref", "")))
            sub = html.escape(_short(r.get("sub", "")))
            mark = "[x]" if r.get("match") else "[ ]"
            body.append(f"<tr><td>{mark}</td><td><code>{call}</code></td>"
                        f"<td><code>{ref}</code></td>"
                        f"<td><code>{sub}</code></td></tr>")
        if not body:
            return ""
        return ("<table class='behavdiff'>"
                "<tr><th></th><th>sample input</th>"
                "<th>reference</th><th>yours</th></tr>"
                + "".join(body) + "</table>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def diff_css() -> str:
    """Raw declarations only (no <style> tags); palette tokens."""
    return (".behavdiff{border-collapse:collapse;font-size:smaller;}"
            ".behavdiff td,.behavdiff th{border:1px solid var(--ink);"
            "padding:2px 6px;}")


def _demo() -> str:
    """Live measured demo table; parse-only fallback; never raises."""
    try:
        from . import sandbox as sbmod
        ref = "def add(a, b):\n    return a + b"
        sub = "def add(a, b):\n    total = a + b\n    return total"
        tests = ("_out = repr(add(2, 3))\n"
                 "assert _out == '5', f'FAIL: {_out}'\nprint('OK')")
        rows = sample_rows(ref, sub, tests, sbmod.SandboxRunner())
        if rows:
            return rows_html(rows)
    except Exception:  # noqa: BLE001 -- demo falls back below
        pass
    try:
        calls = sample_calls("_out = repr(add(2, 3))\n"
                             "assert _out == '5'\nprint('OK')")
        shown = ", ".join(html.escape(c) for c in calls) or "none"
        return (f"<p><small>Sample inputs parsed from the harness: "
                f"<code>{shown}</code> (live run unavailable).</small></p>")
    except Exception:  # noqa: BLE001
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch26 home module."""
    try:
        demo = _demo()
    except Exception:  # noqa: BLE001 -- status must always render
        demo = ""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Refactor behavior-diff <small>(improvement)</small></h3>"
        "<p>Refactor cards (<code>exercises.grade</code>, type 19) used to pass "
        "with a bare verdict. <code>groundwork/behavdiff.py</code> appends a "
        "behavior-diff: the harness sample call runs against BOTH the reference "
        "and your version in the existing sandbox, and the two measured outputs "
        "render side by side -- proof the refactor kept behavior, or the exact "
        "sample where it diverged. Nothing measurable means no extra line, so "
        "legacy feedback stays byte-identical. A live measured sample renders "
        "below.</p>"
        f"{demo}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "refactor-behavior-diff",
        "kind": "improvement",
        "title": "Refactor behavior-diff",
        "blurb": "Your refactor vs the original: measured outputs side by side on the same sample inputs.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
