"""Trace tables: pre-filled step rows + per-cell feedback (I-165).

Type-9 (trace-variable) cards fail as a whole with one feedback line.
This module is display-side only: `table_rows_html` pre-renders the
step-number and source-line columns so learners fill only value cells,
and `per_cell`/`summary_line` explain a type-9 verdict step by step.
Never grades: pass/fail stays owned by exercises.grade (t==9 branch);
cell marks reuse its verdict, so the two can never disagree.
No-data fallback: no expected steps -> table_rows_html "" (caller
renders legacy bytes) and per_cell [] / summary_line "" (grader
feedback byte-identical when detail is disabled). Pure, stdlib only.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b25-tracetable"


def _steps(payload) -> list:
    if not isinstance(payload, dict):
        return []
    try:
        return [str(x) for x in payload.get("expected", [])]
    except TypeError:
        return []


def table_rows_html(payload: dict) -> str:
    """<tr> rows: Step + Line pre-filled, value cell keeps legacy s{i}."""
    steps = _steps(payload)
    if not steps:
        return ""
    try:
        lines = str(payload.get("code", "")).splitlines()
        var = html.escape(str(payload.get("var", "x")))
        out = [f"<tr><th>Step</th><th>Line</th><th>{var}</th></tr>"]
        for i in range(len(steps)):
            line = html.escape(lines[i] if i < len(lines) else "")
            out.append(f"<tr><td>{i + 1}</td><td><code>{line}</code></td>"
                       f"<td><input name='s{i}' size='12'></td></tr>")
        return "".join(out)
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def split_answers(expected: list, submission: str) -> list:
    """Same parse as the t==9 grader: lines, or comma/space tokens."""
    given = [l.strip() for l in str(submission).splitlines() if l.strip()]
    if len(given) == 1 and len(expected) > 1:
        given = [x.strip() for x in given[0].replace(",", " ").split()]
    return given


def per_cell(expected: list, submission: str) -> list:
    """One {step, passed, given, want} per expected step; [] when none."""
    exp = [str(x) for x in (expected or [])]
    if not exp:
        return []
    try:
        given = split_answers(exp, submission)
    except Exception:  # noqa: BLE001 -- display never breaks grading
        return []
    return [{"step": i + 1, "passed": (given[i] if i < len(given) else "") == w,
             "given": given[i] if i < len(given) else "", "want": w}
            for i, w in enumerate(exp)]


def summary_line(rows: list, n_extra: int = 0) -> str:
    """'2/3 steps right -- step 2: expected '3', you gave '4''; '' if none."""
    if not rows:
        return ""
    try:
        bad = [r for r in rows if not r.get("passed")]
        if not bad and not n_extra:
            return f"All {len(rows)} steps right."
        bits = [f"step {r['step']}: expected {r['want']!r}, "
                f"you gave {r['given']!r}" for r in bad]
        if n_extra:
            bits.append(f"{n_extra} extra value(s)")
        return (f"{len(rows) - len(bad)}/{len(rows)} steps right -- "
                + "; ".join(bits) + ".")
    except Exception:  # noqa: BLE001 -- summary must never raise
        return ""


def cells_html(rows: list) -> str:
    """Escaped <ul>: [+] per passed cell, [!] + expected-vs-yours per miss."""
    if not rows:
        return ""
    try:
        items = []
        for r in rows:
            g = html.escape(str(r.get("given", ""))[:60])
            if r.get("passed"):
                items.append(f"<li>[+] Step {r['step']} -- <code>{g}</code></li>")
            else:
                w = html.escape(str(r.get("want", ""))[:60])
                items.append(f"<li>[!] Step {r['step']} -- expected <code>{w}</code>, "
                             f"you gave <code>{g}</code></li>")
        return "<ul class='trace-cells'>" + "".join(items) + "</ul>"
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for trace tables."""
    return {"id": "trace-tables", "kind": "improvement",
            "title": "Trace tables",
            "blurb": ("Trace cards pre-fill each step row with its line; a "
                      "miss marks every cell so you see exactly which step "
                      "diverged."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    rows = per_cell(["1", "3", "9"], "1\n4\n9")
    return (f"<h3 id='{STATUS_ANCHOR}'>Trace tables "
            f"<small>(improvement)</small></h3>"
            f"<p>{html.escape(summary_line(rows))} "
            f"<code>groundwork/tracetable.py</code>.</p>"
            f"{cells_html(rows)}")
