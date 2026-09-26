"""Click-to-pair alternative for match-pairs cards (I-164).

Type 30 posts ``m<i>=<letter>`` inputs; ``web._parse_review_form`` folds
them into ``i=LETTER`` lines and ``exercises.grade`` (type-30 branch)
parses them with ``_parse_keyed``. This module adds tap-to-pair buttons
that write into those SAME typing inputs, so grading is untouched and
no duplicate field names are posted. No-JS renders the typing flow
alone; empty sides render "" (byte-identical legacy).
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b25-matchpair"


def letter_for(right: list, value: str) -> str:
    """Letter of value in right list, '' when absent. Never raises."""
    try:
        return chr(ord("A") + list(right).index(value))
    except (ValueError, TypeError):
        return ""


def serialize(pairs: dict) -> str:
    """{row: letter} -> ``i=LETTER`` lines (sorted, stripped, upper)."""
    items = []
    try:
        entries = (pairs or {}).items()
    except AttributeError:
        return ""
    for k, v in entries:
        try:
            items.append((int(k), str(v).strip().upper()))
        except (TypeError, ValueError):
            continue
    return "\n".join(f"{i}={L}" for i, L in sorted(items) if L)


def pair_html(cid, left, right) -> str:
    """Clickable left/right buttons syncing into the typing inputs.

    Click a left item (selects), then a right item (pairs: writes its
    letter into that row's ``m<i>`` typing input). Click a paired
    right button again to clear. "" when either side is empty.
    """
    try:
        rows = list(left or [])
        cols = list(right or [])
        if not rows or not cols:
            return ""
        c = html.escape(str(cid), quote=True)
        lb = "".join(
            f"<button type='button' data-mp='l' data-c='{c}' data-i='{i}'"
            f" aria-pressed='false'><b>{i}</b> {html.escape(str(a))}</button>"
            for i, a in enumerate(rows))
        rb = "".join(
            f"<button type='button' data-mp='r' data-c='{c}'"
            f" data-L='{chr(ord('A') + i)}'>"
            f"<b>{chr(ord('A') + i)}</b> {html.escape(str(b))}</button>"
            for i, b in enumerate(cols))
        return (f"<div class='mpair' id='mp-{c}'>"
                f"<div class='mp-l'>{lb}</div>"
                f"<div class='mp-r'>{rb}</div>"
                f"<button type='button' data-mp='clear' data-c='{c}'>"
                f"Clear pairs</button></div>{PAIR_JS}")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


PAIR_JS = """
<script>
if (!window.__mpInit) { window.__mpInit = true;
document.addEventListener('click', function (e) {
  var b = e.target.closest('button[data-mp]'); if (!b) return;
  var box = b.closest('.mpair'); if (!box) return;
  var form = b.closest('form');
  function typed(i) {
    return form ? form.querySelector('input[name=\"m' + i + '\"]') : null;
  }
  if (b.getAttribute('data-mp') === 'clear') {
    box.querySelectorAll('button[data-mp]').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
    if (form) form.querySelectorAll('input[name^=\"m\"]').forEach(function (h) { h.value = ''; });
    return;
  }
  if (b.getAttribute('data-mp') === 'l') {
    var on = b.getAttribute('aria-pressed') === 'true';
    box.querySelectorAll('button[data-mp=\"l\"]').forEach(function (x) { x.setAttribute('aria-pressed', 'false'); });
    b.setAttribute('aria-pressed', on ? 'false' : 'true'); return;
  }
  var sel = box.querySelector('button[data-mp=\"l\"][aria-pressed=\"true\"]');
  if (!sel) return;
  var h = typed(sel.getAttribute('data-i'));
  if (!h) return;
  var L = b.getAttribute('data-L');
  h.value = (h.value === L) ? '' : L;
  b.setAttribute('aria-pressed', h.value ? 'true' : 'false');
});
}
</script>"""


def tour_entry() -> dict:
    """Tour registry entry for click-to-pair matching."""
    return {"id": "match-click-pair", "kind": "improvement",
            "title": "Click-to-pair matching",
            "blurb": ("Match-pairs cards pair by tapping left then right — "
                      "no more letter typing; typed boxes stay as fallback."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    return (f"<h3 id='{STATUS_ANCHOR}'>Click-to-pair match-pairs "
            f"<small>(improvement)</small></h3>"
            f"<p>Tap a left item, then its right partner — pairs land in the "
            f"same <code>m&lt;i&gt;</code> fields the letter grader reads. "
            f"<code>groundwork/matchpair.py</code>.</p>"
            + pair_html("demo", ["timeout", "retries"], ["config", "policy"]))
