"""Predict-output pre-submit retries: 3 strikes, shrinking hints (I-166).

Type-8 cards grade pass/fail at submit (exercises.grade t==8). This module
adds up to 3 CLIENT-SIDE pre-submit checks ("Try it" button compares the
typed guess to the stored expected output in JS widget state — no POST, no
schema change). Each miss unlocks a narrower hint tier. Grade path untouched.
"""
from __future__ import annotations

import html
import json

STATUS_ANCHOR = "status-b25-predtry"
MAX_TRIES = 3


def _payload_of(card) -> dict:
    try:
        if isinstance(card, dict) and "payload" in card:
            return json.loads(card.get("payload") or "{}")
        if isinstance(card, dict):
            return card
        try:
            raw = card["payload"]
        except (KeyError, IndexError, TypeError):
            return {}
        return json.loads(raw or "{}")
    except (ValueError, TypeError):
        pass
    return {}


def reference_output(payload) -> str:
    """Stored expected output or '' (same gate as sandout.measured_output)."""
    try:
        if not isinstance(payload, dict):
            return ""
        code, exp = payload.get("code", ""), payload.get("expected", "")
        if not isinstance(code, str) or not isinstance(exp, str):
            return ""
        if not code.strip() or not exp.strip():
            return ""
        return exp.strip()
    except Exception:  # noqa: BLE001 -- gate must never raise
        return ""


def _lines(t):
    return str(t).replace("\r\n", "\n").replace("\r", "\n").splitlines()


def tier1_shape(expected) -> str:
    """Strike 1: output shape/length only. '' on hostile input."""
    try:
        if not isinstance(expected, str):
            return ""
        t = str(expected)
        ls = _lines(t)
        return f"Expected {len(ls)} line(s), {len(t)} char(s)."
    except Exception:  # noqa: BLE001 -- hint must never raise
        return ""


def tier2_position(expected, guess):
    """Strike 2: (line, char) 1-based of first difference; None if match."""
    try:
        a, b = _lines(expected), _lines(guess)
        for i in range(max(len(a), len(b))):
            x, y = a[i] if i < len(a) else "", b[i] if i < len(b) else ""
            if x != y:
                c = next((k for k, (p, q) in enumerate(zip(x, y)) if p != q),
                         min(len(x), len(y)))
                return (i + 1, c + 1)
        return None if len(a) == len(b) else (min(len(a), len(b)) + 1, 1)
    except Exception:  # noqa: BLE001 -- hint must never raise
        return None


def tier2_hint(expected, guess) -> str:
    """Strike 2 text: first-difference position; '' when matched."""
    pos = tier2_position(expected, guess)
    return f"First differs at line {pos[0]}, char {pos[1]}." if pos else ""


def tier3_region(expected, guess, ctx: int = 40) -> str:
    """Strike 3: quote of expected text around first difference."""
    try:
        pos = tier2_position(expected, guess)
        if pos is None:
            return ""
        flat = str(expected).replace("\r\n", "\n").replace("\r", "\n")
        off = sum(len(l) + 1 for l in _lines(expected)[:pos[0] - 1]) + pos[1] - 1
        s, e = max(0, off - ctx // 2), min(len(flat), off + ctx // 2)
        return "Near miss — expected reads: …" + flat[s:e] + "…"
    except Exception:  # noqa: BLE001 -- hint must never raise
        return ""


def hint_for(expected, guess, strike: int) -> str:
    """Tier text for strike 1..3; '' when matched, exhausted, or hostile."""
    try:
        n = int(strike)
        if n < 1 or n > MAX_TRIES:
            return ""
        if str(expected).strip() == str(guess).strip():
            return ""
        if n == 1:
            return tier1_shape(expected)
        if n == 2:
            return tier2_hint(expected, guess)
        return tier3_region(expected, guess)
    except Exception:  # noqa: BLE001 -- hint must never raise
        return ""


def tries_html(card) -> str:
    """Pre-submit affordance; '' when no reference (legacy fallback)."""
    try:
        ref = reference_output(_payload_of(card))
        if not ref:
            return ""
        t1 = html.escape(tier1_shape(ref))
        return ("<span class='predtry' data-expected='"
                + html.escape(ref, quote=True) + "' data-tries='0'>"
                "<button type='button' class='predtry-try'>Try without submitting</button>"
                f"<small class='predtry-hint' data-t1=\"{t1}\">3 pre-submit tries; each miss narrows the hint.</small></span>"
                "<script>if(!window.__predtry){window.__predtry=true;document.addEventListener('click',function(e){"
                "var b=e.target.closest('.predtry-try');if(!b)return;var w=b.closest('.predtry');"
                "var t=+w.dataset.tries;if(t>=3)return;var g=w.closest('form').querySelector('input[name=answer]').value;"
                "var ref=w.dataset.expected;if(g.trim()===ref.trim()){w.querySelector('.predtry-hint').textContent='Match — submit it.';return;}"
                "t++;w.dataset.tries=t;var h=w.querySelector('.predtry-hint');"
                "if(t===1)h.textContent=w.dataset.t1;"
                "else{var a=ref.split('\\n'),c=g.split('\\n'),ln=0,ch=0;for(var i=0;i<Math.max(a.length,c.length);i++){var x=a[i]||'',y=c[i]||'';if(x!==y){ln=i+1;ch=0;while(ch<Math.min(x.length,y.length)&&x[ch]===y[ch])ch++;ch++;break;}}"
                "if(t===2)h.textContent='First differs at line '+ln+', char '+ch+'.';"
                "else{var f=ref.split('\\n').slice(0,ln).join('\\n');var o=f.length;h.textContent='Near miss — expected reads: …'+ref.slice(Math.max(0,o-20),o+20)+'…';}}"
                "if(t>=3)b.disabled=true;});}</script>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for predict retries."""
    return {"id": "predict-retries", "kind": "improvement",
            "title": "Predict retries: 3 strikes",
            "blurb": ("Try a prediction 3 times pre-submit; each miss "
                      "narrows the hint."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch25.py."""
    try:
        return (f"<h3 id='{STATUS_ANCHOR}'>Predict retries "
                "<small>(improvement)</small></h3>"
                "<p>Three pre-submit tries on type-8 cards "
                "(<code>cards.answer_widget</code>): each miss unlocks a "
                "narrower hint — shape, position, region quote — computed "
                "client-side from the stored expected output. No schema "
                "change; submit/grade untouched.</p>"
                f"<p><small>Sample tier-1: {html.escape(tier1_shape('a\nb'))}</small></p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Predict retries</h3>"
                "<p>Help unavailable.</p>")
