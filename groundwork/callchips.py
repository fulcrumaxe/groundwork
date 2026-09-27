"""Click-to-order chips for call-path-trace cards (I-173).

Type 10 posts the call order in the hidden drag-synced `answer`
field, with the typed `answer_text` box as the no-JS fallback;
`web._parse_review_form` reads the non-blank `answer` value first,
else the first `answer_text` value. This module adds tap-to-order
chips that write tapped indices into those SAME two inputs, so
`exercises._grade_order` is untouched and no duplicate field names
are posted (precedent: matchpair.py writes into the existing `m<i>`
typing inputs). Tapping a picked chip again unpicks it; Clear
empties both inputs. A later drag overwrites the hidden field
(last action wins); taps never touch the drag list. No-JS renders
the drag + typing flow alone; empty lines render "" (byte-identical
legacy). Etype 11 Parsons code lines are out of scope.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b26-callchips"


def _as_list(lines) -> list:
    try:
        return list(lines) if isinstance(lines, (list, tuple)) else []
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return []


def parse_order(text, n: int) -> list:
    """In-range indices from an order string; bad tokens dropped."""
    try:
        count = int(n)
    except (TypeError, ValueError):
        return []
    picked = []
    for tok in str(text or "").replace(",", " ").split():
        try:
            i = int(tok)
        except ValueError:
            continue
        if 0 <= i < count and i not in picked:
            picked.append(i)
    return picked


def tap(current, i, n: int) -> str:
    """Order string after tapping chip i: appends, or unpicks."""
    try:
        count = int(n)
        idx = int(i)
    except (TypeError, ValueError):
        return " ".join(str(x) for x in parse_order(current, n))
    picked = parse_order(current, count)
    if idx < 0 or idx >= count:
        return " ".join(str(x) for x in picked)
    if idx in picked:
        picked.remove(idx)
    else:
        picked.append(idx)
    return " ".join(str(x) for x in picked)


def chips_html(cid, lines) -> str:
    """Tap-to-order chips syncing into the existing order inputs.

    One button per line: tapping appends its index to the hidden
    `answer` field and mirrors it into `answer_text`. "" when empty.
    """
    try:
        rows = _as_list(lines)
        if not rows:
            return ""
        c = html.escape(str(cid), quote=True)
        btns = "".join(
            f"<button type='button' data-cc='{i}' data-c='{c}'"
            f" aria-pressed='false'><b>{i}</b>"
            f" {html.escape(str(name))} <span data-pos=''></span></button>"
            for i, name in enumerate(rows))
        return (f"<div class='corder' id='cc-{c}' data-tapped=''>"
                f"<p>Tap the calls in order (entry point first):</p>"
                f"<div class='cc-chips'>{btns}</div>"
                f"<button type='button' data-cc='clear' data-c='{c}'>"
                f"Clear order</button></div>{CHIPS_JS}")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


CHIPS_JS = """
<script>
if (!window.__ccInit) { window.__ccInit = true;
document.addEventListener('click', function (e) {
  var b = e.target.closest('button[data-cc]'); if (!b) return;
  var box = b.closest('.corder'); if (!box) return;
  var form = b.closest('form'); if (!form) return;
  var hid = form.querySelector('input[name="answer"][type="hidden"]');
  var typed = form.querySelector('input[name="answer_text"]');
  function order() {
    var v = hid ? hid.value : '';
    return v.replace(/,/g, ' ').split(/\\s+/).filter(function (x) { return x !== ''; });
  }
  function write(vals) {
    var s = vals.join(' ');
    if (hid) hid.value = s;
    if (typed) typed.value = s;
    box.querySelectorAll('button[data-cc]').forEach(function (x) {
      var k = x.getAttribute('data-cc');
      if (k === 'clear') return;
      var at = vals.indexOf(k);
      x.setAttribute('aria-pressed', at >= 0 ? 'true' : 'false');
      var slot = x.querySelector('span[data-pos]');
      if (slot) slot.textContent = at >= 0 ? ('#' + (at + 1)) : '';
    });
  }
  if (b.getAttribute('data-cc') === 'clear') { write([]); return; }
  var vals = box.getAttribute('data-tapped') ? order() : [];
  box.setAttribute('data-tapped', '1');
  var k = b.getAttribute('data-cc');
  var at = vals.indexOf(k);
  if (at >= 0) vals.splice(at, 1); else vals.push(k);
  write(vals);
});
}
</script>"""


def tour_entry() -> dict:
    """Tour registry entry for click-to-order call paths."""
    return {"id": "callpath-click-order", "kind": "improvement",
            "title": "Click-to-order call paths",
            "blurb": ("Call-path cards order by tapping chips entry-first -- "
                      "no more index typing; drag and typed boxes stay as "
                      "fallback."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch26.py."""
    return (f"<h3 id='{STATUS_ANCHOR}'>Click-to-order call paths "
            f"<small>(improvement)</small></h3>"
            f"<p>Tap the call chips in order -- taps land in the same "
            f"<code>answer</code> + <code>answer_text</code> fields the "
            f"order grader reads. <code>groundwork/callchips.py</code>.</p>"
            + chips_html("demo", ["serve", "grade", "store"]))
