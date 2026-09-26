"""Learner-vs-expected output diff (I-157): side-by-side mismatch view.

Predict-output cards (``exercises.grade`` type 8) fail today with a
single-line ``Actual output: ...`` repr that shows only the sandbox
side. This module aligns the learner's lines against the expected
lines and renders the divergence side by side: plain text for the
grade feedback string, HTML for richer result screens. Matching
outputs and hostile input render as the empty string, so the caller
keeps its legacy feedback byte-identical on those paths. Stdlib
only (``difflib``, ``html``); never raises.
"""
from __future__ import annotations

import difflib
import html

STATUS_ANCHOR = "status-b24-outdiff"

MAX_ROWS = 20
MAX_TEXT_PAIRS = 8


def normalize_output(value) -> str:
    """Comparable output text; "" for missing/hostile input."""
    try:
        if value is None:
            return ""
        if isinstance(value, str):
            text = value
        else:
            text = str(value)
        return text.replace("\r\n", "\n").replace("\r", "\n")
    except Exception:  # noqa: BLE001 -- normalizing never raises
        return ""


def rows(got, want) -> list:
    """Aligned row pairs for the two outputs.

    Each row is ``(got_no, want_no, got, want, same)``: 1-based line
    numbers with ``None`` on the unused side, ``None`` text where a
    side has no line, and ``same`` marking equal pairs. Empty on
    hostile input. Never raises.
    """
    try:
        a = normalize_output(got).splitlines()
        b = normalize_output(want).splitlines()
        out = []
        matcher = difflib.SequenceMatcher(a=a, b=b, autojunk=False)
        for tag, i1, i2, j1, j2 in matcher.get_opcodes():
            if tag == "equal":
                for k in range(i2 - i1):
                    out.append((i1 + k + 1, j1 + k + 1,
                                a[i1 + k], b[j1 + k], True))
            elif tag == "delete":
                for k in range(i1, i2):
                    out.append((k + 1, None, a[k], None, False))
            elif tag == "insert":
                for k in range(j1, j2):
                    out.append((None, k + 1, None, b[k], False))
            else:  # replace: pair lines off against each other, in order.
                n = max(i2 - i1, j2 - j1)
                for k in range(n):
                    gi = i1 + k if i1 + k < i2 else None
                    wj = j1 + k if j1 + k < j2 else None
                    out.append((gi + 1 if gi is not None else None,
                                wj + 1 if wj is not None else None,
                                a[gi] if gi is not None else None,
                                b[wj] if wj is not None else None,
                                False))
        return out
    except Exception:  # noqa: BLE001
        return []


def has_mismatch(got, want) -> bool:
    """True iff the two outputs differ; False on hostile input."""
    try:
        return normalize_output(got) != normalize_output(want)
    except Exception:  # noqa: BLE001
        return False


def first_mismatch(got, want):
    """1-based aligned-row number of the first differing pair.

    ``None`` when the outputs match or input is hostile. Never raises.
    """
    try:
        for i, row in enumerate(rows(got, want)):
            if not row[4]:
                return i + 1
        return None
    except Exception:  # noqa: BLE001
        return None


def _show(text) -> str:
    return repr(text) if text is not None else "--"


def _cell(num) -> str:
    return "" if num is None else str(num)


def mismatch_text(got, want, cap: int = MAX_TEXT_PAIRS) -> str:
    """Plain-text side-by-side for the grade feedback string.

    "" when the outputs match or input is hostile, so the caller
    keeps its legacy single line. Never raises.
    """
    try:
        try:
            n = int(cap)
        except (TypeError, ValueError):
            n = MAX_TEXT_PAIRS
        pairs = [r for r in rows(got, want) if not r[4]]
        if not pairs:
            return ""
        head = f"Output differs at row {first_mismatch(got, want)}: yours vs expected:"
        shown = pairs[:max(0, n)]
        lines = [head] + [
            f"yours[{_cell(g)}] {_show(t)} | expected[{_cell(w)}] {_show(e)}"
            for g, w, t, e, _ in shown]
        if len(pairs) > len(shown):
            lines.append(f"... and {len(pairs) - len(shown)} more differing rows")
        return "\n".join(lines)
    except Exception:  # noqa: BLE001 -- feedback never raises
        return ""


def mismatch_html(got, want, cap: int = MAX_ROWS) -> str:
    """Side-by-side HTML table; "" when outputs match or input is hostile."""
    try:
        try:
            n = int(cap)
        except (TypeError, ValueError):
            n = MAX_ROWS
        pairs = [r for r in rows(got, want) if not r[4]]
        shown = pairs[:max(0, n)]
        if not shown:
            return ""
        first = first_mismatch(got, want)
        body = "".join(
            f"<tr class='outdiff-diff'><td>{_cell(g)}</td>"
            f"<td>{html.escape(t) if t is not None else '--'}</td>"
            f"<td>{_cell(w)}</td>"
            f"<td>{html.escape(e) if e is not None else '--'}</td></tr>"
            for g, w, t, e, _ in shown)
        extra = (f"<caption>First differs at row {first} "
                 f"(+{len(pairs) - len(shown)} more)</caption>"
                 if len(pairs) > len(shown)
                 else f"<caption>First differs at row {first}</caption>")
        return (
            f"<table class='outdiff'>{extra}"
            "<tr><th>yours#</th><th>yours</th>"
            "<th>expected#</th><th>expected</th></tr>"
            f"{body}</table>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def diff_css() -> str:
    """Raw declarations only (no <style> tags); palette tokens."""
    return (".outdiff{border-collapse:collapse;font-size:smaller;}"
            ".outdiff-diff{color:var(--ink);background:var(--paper);}")


def section_html() -> str:
    """Anchored status subsection; joined by the batch24 home module."""
    sample = mismatch_html("a\nb\n", "a\nB\n")
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Output mismatch side-by-side <small>(improvement)</small></h3>"
        "<p>When a predicted output misses, the result path "
        "(<code>exercises.grade</code>, type 8) shows yours against "
        "expected line by line instead of a one-line repr. "
        "<code>groundwork/outdiff.py</code> renders nothing when the "
        "outputs match or the reference is missing, so legacy feedback "
        "stays byte-identical. A live sample renders below.</p>"
        f"{sample}"
    )


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "output-mismatch-diff",
        "kind": "improvement",
        "title": "Output mismatch side-by-side",
        "blurb": "Wrong prediction? Yours vs expected, line by line.",
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
