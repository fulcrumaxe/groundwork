"""Odd-one-out strike-through elimination before committing (I-175).

Type-18 cards post one shared field: each choice renders as
<button name='answer' value='<choice>'> (cards.answer_widget,
etype 18 branch) and exercises.grade t==18 compares the posted text
to the stored answer. This module adds pre-commit CLIENT-SIDE
elimination toggles ("Rule out: [1] [2] [3]") that paint
strike-through on ruled-out choices. Paint only, per the predtry
precedent: toggles are type='button' with no name (never post, never
submit), answer buttons keep identical name/value markup and stay
submittable, so a wrongly ruled-out choice can still be committed.
Grade path untouched; no schema change.
"""
from __future__ import annotations

import html
import json

STATUS_ANCHOR = "status-b26-xout"


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


def etype_of(card) -> str:
    """Card exercise type as str; '' on hostile input."""
    try:
        if isinstance(card, dict):
            return str(card.get("exercise_type", ""))
        return str(card["exercise_type"])
    except (KeyError, IndexError, TypeError):
        return ""
    except Exception:  # noqa: BLE001 -- gate must never raise
        return ""


def choices_of(card) -> list:
    """Odd-one-out choice texts; [] unless etype 18 with 2+ str choices."""
    try:
        if etype_of(card) != "18":
            return []
        raw = _payload_of(card).get("choices", [])
        if not isinstance(raw, list) or len(raw) < 2:
            return []
        if any(not isinstance(c, str) for c in raw):
            return []
        return list(raw)
    except Exception:  # noqa: BLE001 -- gate must never raise
        return []


def left_text(left: int, total: int) -> str:
    """Rule-out counter line; hostile input fails closed to ''."""
    try:
        n, t = int(left), int(total)
        if t < 0 or n < 0 or n > t:
            return ""
        if n == 0:
            return "all ruled out - reset or commit anyway"
        return f"{n} of {t} left"
    except (TypeError, ValueError):
        return ""
    except Exception:  # noqa: BLE001 -- text must never raise
        return ""


def elim_js() -> str:
    """Delegated strike-through painter; single global guard."""
    return (
        "<script>if(!window.__xout){window.__xout=true;"
        "function xoutPaint(w){var f=w.closest('form');"
        "var bs=f?f.querySelectorAll(\"button[name='answer']\"):[];"
        "var ts=w.querySelectorAll('.xout-t');var n=0;"
        "for(var i=0;i<ts.length;i++){"
        "var out=ts[i].getAttribute('aria-pressed')==='true';"
        "if(i<bs.length){bs[i].style.textDecoration=out?'line-through':'';"
        "bs[i].style.opacity=out?'0.55':'';}"
        "if(!out)n++;}"
        "var c=w.querySelector('.xout-count');"
        "if(c)c.textContent=n===0?'all ruled out - reset or commit anyway':n+' of '+ts.length+' left';}"
        "document.addEventListener('click',function(e){"
        "if(!e.target.closest)return;"
        "var w=e.target.closest('.xout');if(!w)return;"
        "var t=e.target.closest('.xout-t');"
        "if(t){t.setAttribute('aria-pressed',t.getAttribute('aria-pressed')==='true'?'false':'true');xoutPaint(w);return;}"
        "if(e.target.closest('.xout-reset')){"
        "var ts=w.querySelectorAll('.xout-t');"
        "for(var i=0;i<ts.length;i++)ts[i].setAttribute('aria-pressed','false');"
        "xoutPaint(w);}});}</script>"
    )


def elim_html(card) -> str:
    """Rule-out strip for odd-one-out cards; '' otherwise (legacy fallback)."""
    try:
        choices = choices_of(card)
        if len(choices) < 2:
            return ""
        n = len(choices)
        toggles = "".join(
            f"<button type='button' class='xout-t' data-i='{i}' "
            f"aria-pressed='false' title='Rule out choice {i + 1}'>[{i + 1}]</button>"
            for i in range(n))
        return (
            f"<span class='xout'>Rule out: {toggles} "
            f"<button type='button' class='xout-reset'>Reset</button> "
            f"<small class='xout-count' aria-live='polite'>{html.escape(left_text(n, n))}</small></span>"
            + elim_js())
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def tour_entry() -> dict:
    """Tour registry entry for odd-one-out elimination."""
    return {"id": "odd-one-out-xout", "kind": "improvement",
            "title": "Odd-one-out elimination",
            "blurb": ("Rule out odd-one-out choices with strike-through "
                      "before committing - paint only, grading untouched."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by the batch26 home module."""
    try:
        demo = elim_html({"id": "demo", "exercise_type": 18,
                          "payload": json.dumps(
                              {"choices": ["call_a", "call_b", "outsider"],
                               "answer": "outsider"})})
        return (f"<h3 id='{STATUS_ANCHOR}'>Odd-one-out elimination "
                "<small>(improvement)</small></h3>"
                "<p>Type-18 cards gain a pre-commit rule-out strip "
                "(<code>cards.answer_widget</code> etype 18 branch): toggle "
                "[1] [2] [3] to strike through ruled-out choices, Reset to "
                "restore. Toggles are nameless type='button' controls so "
                "they never post; answer buttons keep identical name/value "
                "markup and stay submittable. No schema change; "
                "submit/grade untouched.</p>"
                f"<p><small>Live demo (toggles paint only here):</small> {demo}</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Odd-one-out elimination</h3>"
                "<p>Help unavailable.</p>")
