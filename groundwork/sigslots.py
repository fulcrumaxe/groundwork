"""Signature skeleton with per-param slots and ticks (I-179).

Etype-3 (signature-recall) cards grade pass/fail on the whole typed
line (exercises.grade t==3), so one wrong parameter fails the card
without saying which. This module renders the stored signature as an
advisory skeleton -- func name plus one slot per parameter, each with
its own tick -- beside the unchanged Write-it input; a small client
script ticks each slot whose name appears as a whole word in the typed
text. Advisory only: no posted field changes, grading untouched. Pure
functions, stdlib only, no DB, never raise.
"""
from __future__ import annotations

import html
import json
import re

STATUS_ANCHOR = "status-b27-sigslots"
ETYPE = "3"


def _field(card, name, default=""):
    """card[name] for dicts and sqlite Rows; default when missing."""
    try:
        return card[name]
    except (KeyError, IndexError, TypeError):
        try:
            return card.get(name, default)
        except AttributeError:
            return default


def signature_for(card) -> str:
    """Stored signature for the card; "" when absent/hostile."""
    try:
        p = _field(card, "payload", {})
        if isinstance(p, str):
            try:
                p = json.loads(p or "{}")
            except ValueError:
                return ""
        if not isinstance(p, dict):
            return ""
        sig = p.get("signature", "")
        return sig if isinstance(sig, str) else ""
    except Exception:  # noqa: BLE001 -- lookup must never raise
        return ""


def _split_top(body: str) -> list:
    """Split on top-level commas; string/quote aware, never raises."""
    parts, depth, cur, quote = [], 0, [], ""
    esc = False
    try:
        for ch in body:
            if quote:
                cur.append(ch)
                if esc:
                    esc = False
                elif ch == "\\":
                    esc = True
                elif ch == quote:
                    quote = ""
                continue
            if ch in ("'", '"'):
                quote, esc = ch, False
                cur.append(ch)
            elif ch in "([{":
                depth += 1
                cur.append(ch)
            elif ch in ")]}":
                depth = max(0, depth - 1)
                cur.append(ch)
            elif ch == "," and depth == 0:
                parts.append("".join(cur))
                cur = []
            else:
                cur.append(ch)
        parts.append("".join(cur))
        return parts
    except Exception:  # noqa: BLE001 -- split must never raise
        return []


def _clean_param(piece: str) -> str:
    """One parameter name: strip annotation/default/stars; "" if none."""
    try:
        name = piece.split("=", 1)[0].split(":", 1)[0].strip()
        name = name.lstrip("*").strip()
        return name if name.isidentifier() else ""
    except Exception:  # noqa: BLE001 -- cleaner must never raise
        return ""


def params_of(signature) -> list:
    """Parameter names in order; [] when unparseable/hostile."""
    try:
        if not isinstance(signature, str) or "(" not in signature:
            return []
        inner = signature.split("(", 1)[1].rsplit(")", 1)[0]
        if not inner.strip():
            return []
        return [n for n in (_clean_param(p) for p in _split_top(inner))
                if n]
    except Exception:  # noqa: BLE001 -- parse must never raise
        return []


def func_of(signature) -> str:
    """Function name before the parens; "" when hostile."""
    try:
        if not isinstance(signature, str) or "(" not in signature:
            return ""
        head = signature.split("(", 1)[0].strip()
        head = re.sub(r"^def\s+", "", head).strip()
        name = head.split(".")[-1].strip()
        return name if name.isidentifier() else ""
    except Exception:  # noqa: BLE001 -- parse must never raise
        return ""


def ticks(typed, params) -> dict:
    """Server mirror of client ticking: {param: whole-word present}."""
    try:
        text = typed if isinstance(typed, str) else ""
        names = list(params) if isinstance(params, (list, tuple)) else []
        out = {}
        for p in names:
            try:
                if not isinstance(p, str) or not p:
                    continue
                out[p] = re.search(r"\b" + re.escape(p) + r"\b",
                                   text) is not None
            except re.error:
                out[p] = False
        return out
    except Exception:  # noqa: BLE001 -- scan must never raise
        return {}


def skeleton_html(cid, signature, enabled: bool = True) -> str:
    """Advisory skeleton: name plus one ticked slot per param.

    Display spans only -- no inputs, nothing posted. "" when off,
    unparseable, or parameterless (legacy fallback).
    """
    try:
        if not enabled:
            return ""
        params = params_of(signature)
        if not params:
            return ""
        func = func_of(signature)
        prefix = f"{html.escape(func)}(" if func else "("
        slots = ", ".join(
            f"<span class='sigslot' "
            f"data-param='{html.escape(p, quote=True)}'>"
            f"<span aria-hidden='true'>[ ]</span> "
            f"<code>{html.escape(p)}</code></span>"
            for p in params)
        c = html.escape(str(cid), quote=True)
        return (f"<span class='sigskel' id='ss-{c}'>"
                f"<small>Signature skeleton (advisory):</small> "
                f"<code>{prefix}</code>{slots}<code>)</code></span>")
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def script_js() -> str:
    """One guarded listener: tick slots from the Write-it box."""
    return """
<script>
if (!window.__sigslotsInit) { window.__sigslotsInit = true;
function sigslotsTick(box) {
  var form = box.closest ? box.closest('form') : null;
  if (!form) return;
  var skel = form.querySelector('.sigskel');
  if (!skel) return;
  var text = box.value || '';
  Array.prototype.forEach.call(skel.querySelectorAll('.sigslot'), function (slot) {
    var param = slot.getAttribute('data-param') || '';
    if (!param) return;
    var esc = param.replace(/[.*+?^${}()|[\\]\\\\]/g, '\\\\$&');
    var on = new RegExp('\\\\b' + esc + '\\\\b').test(text);
    slot.querySelector('span').textContent = on ? '[x]' : '[ ]';
  });
}
document.addEventListener('input', function (e) {
  var box = e.target.closest ? e.target.closest('input[name=answer]') : null;
  if (!box || box.type === 'hidden' || box.type === 'radio' || box.type === 'checkbox') return;
  sigslotsTick(box);
});
}
</script>"""


def enhance(card, body_html: str) -> str:
    """Etype-3 body plus advisory skeleton; legacy bytes otherwise."""
    try:
        etype = str(_field(card, "exercise_type", ""))
    except (AttributeError, TypeError):
        return body_html
    if etype != ETYPE:
        return body_html
    try:
        cid = _field(card, "id", "")
        skel = skeleton_html(cid, signature_for(card))
    except Exception:  # noqa: BLE001 -- enhance must never raise
        return body_html
    if not skel:
        return body_html
    return skel + body_html + script_js()


def tour_entry() -> dict:
    """Tour registry entry for the signature skeleton."""
    return {"id": "signature-skeleton", "kind": "improvement",
            "title": "Signature skeleton with per-param ticks",
            "blurb": ("Signature cards show each parameter as its own slot "
                      "that ticks as you type it - advisory, grading unchanged."),
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection with a live-computed sample."""
    try:
        demo = ticks("fetch(url, timeo", ["url", "timeout", "retries"])
        marks = " ".join(f"{k}={'[x]' if v else '[ ]'}"
                         for k, v in demo.items())
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Signature skeleton "
            "<small>(improvement)</small></h3>"
            "<p>Signature-recall cards show the stored signature as one "
            "slot per parameter, each ticking as its name appears in the "
            "Write-it box - advisory only, grading untouched. "
            "<code>groundwork/sigslots.py</code>.</p>"
            f"<p><small>Sample: {html.escape(marks)}</small></p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Signature skeleton</h3>"
                "<p>Help unavailable.</p>")
