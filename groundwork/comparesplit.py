"""Side-by-side compare panes with synced scrolling (I-169).

Type 22 (compare-implementations) shows Version A/B as one stacked
blob; this renders paired scroll panes that stay in step, degrading
to independent panes without JS. Pure HTML builders; never raises.
"""
from __future__ import annotations

import difflib
import html
import re

STATUS_ANCHOR = "status-b25-comparesplit"
MAX_LINES = 60
_FENCE = re.compile(r"\*\*Version ([AB]):\*\*\s*```\w*\n(.*?)```", re.S)
_LEGACY_HINT = "First line: A or B, then your reasons."


def parse_versions(front):
    """(A, B) code from a gen_compare front; ("","") when unparseable."""
    try:
        m = {g[0]: g[1].strip("\n") for g in _FENCE.findall(front or "")}
        a, b = m.get("A", ""), m.get("B", "")
        return (a, b) if a.strip() or b.strip() else ("", "")
    except Exception:  # noqa: BLE001 -- parse must never raise
        return ("", "")


def _norm(v):
    try:
        return "" if v is None else str(v).replace("\r\n", "\n").replace("\r", "\n")
    except Exception:  # noqa: BLE001 -- coercion must never raise
        return ""


def _align(a, b):
    """difflib-padded (text, diff) rows; both sides equal length."""
    la, lb = [], []
    try:
        ops = difflib.SequenceMatcher(a=a, b=b, autojunk=False).get_opcodes()
    except Exception:  # noqa: BLE001 -- align must never raise
        return la, lb
    for tag, i1, i2, j1, j2 in ops:
        if tag == "equal":
            for k in range(i2 - i1):
                la.append((a[i1 + k], 0))
                lb.append((b[j1 + k], 0))
        elif tag == "delete":
            for k in range(i1, i2):
                la.append((a[k], 1))
                lb.append(("", 1))
        elif tag == "insert":
            for k in range(j1, j2):
                la.append(("", 1))
                lb.append((b[k], 1))
        else:
            for k in range(max(i2 - i1, j2 - j1)):
                la.append((a[i1 + k] if i1 + k < i2 else "", 1))
                lb.append((b[j1 + k] if j1 + k < j2 else "", 1))
    return la[:MAX_LINES], lb[:MAX_LINES]


def _pre(rows):
    return "<pre>" + "\n".join(
        html.escape(t) if not d
        else f"<span class='csplit-diff'>{html.escape(t) or ' '}</span>"
        for t, d in rows) + "</pre>"


def _uid(v):
    return "".join(c for c in str(v or "cs1") if c.isalnum()) or "cs1"


def sync_js(uid="cs1"):
    """Two-way scrollTop/scrollLeft link with re-entrancy guard."""
    u = _uid(uid)
    return ("<script>(function(){var a=document.getElementById('%sa'),"
            "b=document.getElementById('%sb');if(!a||!b)return;var l=false;"
            "function link(s,o){s.addEventListener('scroll',function(){"
            "if(l)return;l=true;o.scrollTop=s.scrollTop;"
            "o.scrollLeft=s.scrollLeft;l=false;});}link(a,b);link(b,a);})();"
            "</script>" % (u, u))


def panes_html(left, right, lt="Version A", rt="Version B", uid="cs1"):
    """Paired panes + sync script; "" when both sides blank/hostile."""
    try:
        a, b = _norm(left).splitlines(), _norm(right).splitlines()
        if not a and not b:
            return ""
        u = _uid(uid)
        la, lb = _align(a, b)
        return (f"<div class='csplit'><div><b>{html.escape(str(lt))}</b>"
                f"<div class='csplit-pane' id='{u}a'>{_pre(la)}</div></div>"
                f"<div><b>{html.escape(str(rt))}</b>"
                f"<div class='csplit-pane' id='{u}b'>{_pre(lb)}</div></div></div>"
                + sync_js(u))
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def split_css():
    """Raw flex-pane declarations (never <style>); head wire joins."""
    return (".csplit{display:flex;gap:8px;}.csplit>div{flex:1;min-width:0;}"
            ".csplit-pane{overflow:auto;max-height:22em;"
            "border:1px solid var(--ink);}.csplit-pane pre{margin:0;}"
            ".csplit-diff{font-weight:bold;}")


def _front_of(card) -> str:
    """front text for dicts and sqlite Rows; "" when missing."""
    try:
        if isinstance(card, dict):
            return card.get("front", "") or ""
        return card["front"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def branch_html(card, payload, cid) -> str:
    """Full etype-22 body: panes + legacy textarea, or legacy alone."""
    try:
        from . import cards as cardsmod  # lazy: cards.py calls this branch
        conf = cardsmod._confidence()
        legacy = (f"<textarea name='answer' rows='5' cols='70' "
                  f"placeholder='{_LEGACY_HINT}'></textarea><br>"
                  f"{conf}<button>Submit explanation</button>")
        a, b = parse_versions(_front_of(card))
        panes = panes_html(a, b, uid=f"cs{cid}")
        return panes + legacy if panes else legacy
    except Exception:  # noqa: BLE001 -- branch must never raise
        try:
            from . import cards as cardsmod
            return (f"<textarea name='answer' rows='5' cols='70' "
                    f"placeholder='{_LEGACY_HINT}'></textarea><br>"
                    f"{cardsmod._confidence()}<button>Submit explanation</button>")
        except Exception:  # noqa: BLE001 -- legacy must never raise
            return "<textarea name='answer' rows='5' cols='70'></textarea>"


def tour_entry() -> dict:
    """Tour registry entry for side-by-side compare panes."""
    return {"id": "compare-panes", "kind": "improvement",
            "title": "Side-by-side compare panes",
            "blurb": "A vs B with scrolling that stays in step.",
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    return (f"<h3 id='{STATUS_ANCHOR}'>Compare panes, scrolling in step "
            "<small>(improvement)</small></h3>"
            "<p>Compare cards (<code>exercises.gen_compare</code>, type 22) show "
            "Version A against Version B in paired panes from "
            "<code>groundwork/comparesplit.py</code>; a small script keeps both "
            "scrolled together, and without JS they scroll independently. "
            "Missing versions render the legacy textarea alone.</p>"
            + panes_html("x = 1\ny = 2", "x = 1\ny = 3"))
