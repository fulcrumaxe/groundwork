"""Standard button order: primary action first/left (I-35).

Primary-left in DOM source order (never CSS-reordered) so keyboard
tab order and screen readers meet the primary action first. Helpers
are pure string builders plus a regex auditor; no DB, no schema,
no groundwork imports.
"""
from __future__ import annotations

import re

FORM_RE = re.compile(r"<form\b.*?</form\s*>", re.I | re.S)
SECONDARY_RE = re.compile(r"<a\b|<button\b[^>]*\btype\s*=\s*['\"]button['\"]", re.I)
PRIMARY_RE = re.compile(
    r"<button\b(?![^>]*\btype\s*=\s*['\"]button['\"])[^>]*>|"
    r"<input\b[^>]*\btype\s*=\s*['\"](?:submit|image)['\"][^>]*>", re.I)


def _str(value) -> str:
    if value is None:
        return ""
    return value if isinstance(value, str) else str(value)


def group(primary_html, secondary_htmls=None) -> str:
    """One button row: primary first, secondaries after, space-joined.

    Hostile input never raises: None -> "", non-strings are str()-ed,
    a bare string secondary is treated as one item, non-iterables -> [].
    """
    primary = _str(primary_html)
    secs = secondary_htmls if secondary_htmls is not None else []
    if isinstance(secs, str):
        secs = [secs]
    try:
        items = [_str(s) for s in secs]
    except TypeError:
        items = []
    items = [s for s in items if s]
    if not primary:
        return " ".join(items)
    return " ".join([primary] + items)


def audit(form_html) -> list:
    """Violations of primary-first order, one dict per offending form.

    A form violates when a secondary action (<a…> or
    <button type="button">) precedes the first primary submit control
    (<button> default/submit or <input type=submit/image>), or when a
    primary appears after a secondary. Non-string input -> []. Forms
    with fewer than two action classes never violate. Audit covers
    static source order only — not styling, JS-reordered DOM, or which
    of two equal submits counts as primary.
    """
    if not isinstance(form_html, str) or not form_html:
        return []
    out = []
    for i, m in enumerate(FORM_RE.finditer(form_html)):
        body = m.group(0)
        prim = list(PRIMARY_RE.finditer(body))
        sec = list(SECONDARY_RE.finditer(body))
        if not prim or not sec:
            continue
        first_primary = prim[0].start()
        first_secondary = sec[0].start()
        if first_secondary < first_primary or any(
                p.start() > first_secondary for p in prim):
            out.append({"form": i,
                        "detail": "secondary action precedes primary submit",
                        "snippet": body[:120].replace("\n", " ")})
    return out


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    demo = group("<button>Save entry</button>",
                 ["<a class='btn' href='/journal'>Cancel</a>"])
    return (
        "<h3 id='status-b8-buttons'>Button order <small>(improvement)</small></h3>"
        "<p>Primary action first, secondary links after — in DOM source "
        "order, never CSS-reordered, so keyboard tab order and screen "
        "readers meet the primary action first. "
        "<code>groundwork/buttons.py</code> provides "
        "<code>group()</code> (primary-first row) and "
        "<code>audit()</code> (flags a secondary action placed before "
        "the primary submit).</p>"
        f"<p><form method='post' action='/journal'>{demo}</form></p>"
    )
