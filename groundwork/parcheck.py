"""Parsons partial-order check: longest correct run (I-163).

Ungraded hint for etype 10/11 Due cards: a button + result slot that
reports the longest contiguous run of the current order that also sits
contiguously in the truth order, e.g. "longest correct run: 3 of 6".
The truth rides a hidden unnamed input (never posted) so the check
runs client-side without touching parsons.py; grading still runs
server-side in exercises._grade_order and this never submits. Pure
functions, stdlib only (html), no DB, never raise.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b25-parcheck"


def _as_list(v) -> list:
    try:
        return list(v) if isinstance(v, (list, tuple)) else []
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return []


def longest_correct_run(submitted, truth) -> tuple:
    """(start, length) of longest submitted slice contiguous in truth.

    Truth-adjacency scan: a run extends only when the current item
    immediately follows its predecessor in truth. Empty/unknown input
    fails closed to (0, 0); ties keep the earliest window.
    """
    try:
        sub, tru = _as_list(submitted), _as_list(truth)
        pos = {}
        for i, v in enumerate(tru):
            try:
                if v not in pos:
                    pos[v] = i
            except TypeError:
                continue
        best, cur, cur_start = (0, 0), 0, 0
        for j, item in enumerate(sub):
            try:
                p = pos.get(item)
            except TypeError:
                p = None
            if p is not None and cur and pos.get(sub[j - 1]) == p - 1:
                cur += 1
            elif p is not None:
                cur, cur_start = 1, j
            else:
                cur = 0
            if cur > best[1]:
                best = (cur_start, cur)
        return best
    except Exception:  # noqa: BLE001 -- scan must never raise
        return (0, 0)


def run_from_indices(idx, lines, solution) -> tuple:
    """Resolve index submission (as _grade_order does), then scan."""
    try:
        ls = _as_list(lines)
        ordered = [ls[i] for i in idx]
        return longest_correct_run(ordered, _as_list(solution))
    except Exception:  # noqa: BLE001 -- scan must never raise
        return (0, 0)


def message(length, total) -> str:
    """"longest correct run: N of M"; zeros on hostile input."""
    try:
        return (f"longest correct run: {max(0, int(length))} "
                f"of {max(0, int(total))}")
    except Exception:  # noqa: BLE001 -- message must never raise
        return "longest correct run: 0 of 0"


def truth_indices(lines, solution) -> list:
    """Solution as indices into lines (the data-i space); [] if unmapped."""
    try:
        ls, tru = _as_list(lines), _as_list(solution)
        if not ls or not tru:
            return []
        pos = {}
        for i, v in enumerate(ls):
            try:
                if v not in pos:
                    pos[v] = i
            except TypeError:
                continue
        out = []
        for v in tru:
            try:
                i = pos.get(v)
            except TypeError:
                return []
            if i is None:
                return []
            out.append(i)
        return out
    except Exception:  # noqa: BLE001 -- mapping must never raise
        return []


def check_html(cid, lines, solution, enabled: bool = True) -> str:
    """Button + result slot + hidden truth; "" when off (legacy bytes)."""
    try:
        if not enabled:
            return ""
        tru = truth_indices(lines, solution)
        if not tru:
            return ""
        c = html.escape(str(cid), quote=True)
        truth = " ".join(str(x) for x in tru)
        return (f"<button type='button' data-parcheck='{c}'>"
                f"Check partial order</button> "
                f"<input type='hidden' id='ps-{c}' value='{truth}'>"
                f"<output id='pc-{c}' data-total='{len(tru)}' "
                f"aria-live='polite'></output>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def check_js() -> str:
    """Client-side run-scan; reads li order + hidden truth, never submits."""
    return ("""<script>if(!window.__parcheckInit){window.__parcheckInit=true;"""
            """document.addEventListener('click',function(e){var b=e.target.closest('[data-parcheck]');"""
            """if(!b)return;var c=b.getAttribute('data-parcheck');var ol=document.getElementById('pl-'+c);"""
            """var out=document.getElementById('pc-'+c);var hid=document.getElementById('ps-'+c);"""
            """if(!ol||!out||!hid)return;"""
            """var cur=Array.prototype.map.call(ol.querySelectorAll('li'),function(li){return li.getAttribute('data-i');});"""
            """var tru=hid.value.split(' ').filter(Boolean);"""
            """var pos={},i;for(i=0;i<tru.length;i++)if(!(tru[i] in pos))pos[tru[i]]=i;"""
            """var best=0,run=0;for(i=0;i<cur.length;i++){if(cur[i] in pos&&(run===0||pos[cur[i-1]]===pos[cur[i]]-1))run++;else if(cur[i] in pos)run=1;else run=0;if(run>best)best=run;}"""
            """out.textContent='longest correct run: '+best+' of '+tru.length;});}</script>""")


def tour_entry() -> dict:
    """Tour registry entry for the Parsons partial-order check."""
    return {"id": "parsons-parcheck", "kind": "improvement",
            "title": "Parsons partial-order check",
            "blurb": ("Stuck mid-reorder? 'Check partial order' shows your "
                      "longest correct run without grading or revealing the "
                      "answer — keep that block, move the rest."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    return (f"<h3 id='{STATUS_ANCHOR}'>Parsons partial-order check "
            "<small>(improvement)</small></h3>"
            "<p>Due Parsons cards gain an ungraded 'Check partial order' "
            "button reporting the <code>longest correct run: N of M</code> "
            "— the longest submitted block also contiguous in truth. "
            "<code>groundwork/parcheck.py</code> provides the scan plus the "
            "widget hook; grading still runs server-side.</p>")
