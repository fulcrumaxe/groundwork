"""Inline blank inputs inside rendered cloze code (I-178).

Type-2 cloze cards blank names out of real code: exercises.gen_cloze
stores the marked-up ``template`` (``___(id)`` markers) plus ``blanks``
in the payload. But cards.answer_widget renders each blank as a
detached labeled field below the prompt -- the learner types with no
surrounding code in view. This module substitutes ``<input>`` elements
back into the escaped template at each marker, so blanks are answered
in context, where the generator left the holes.

Due-queue call site (cards.answer_widget, etype-2 branch): wrap the
legacy body with ``enhance()`` -- inline widget when the payload
carries a template, the legacy separate-fields body byte-identical
otherwise. Posted field names (``b<id>``) are unchanged, so
exercises.grade plus the retry/partial flows work untouched.

Pure functions, stdlib only (html, json, re). No I/O, no DB changes.
"""
from __future__ import annotations

import html
import json
import re

STATUS_ANCHOR = "status-b27-clozein"

BLANK_RE = re.compile(r"___\((\d+)\)")


def _payload_of(card_or_payload) -> dict:
    """Payload dict from a bare payload or a card carrying one."""
    if not isinstance(card_or_payload, dict):
        return {}
    raw = card_or_payload.get("payload", card_or_payload)
    if isinstance(raw, dict):
        return raw
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw or "{}")
        except ValueError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    return {}


def _blanks_of(payload: dict) -> dict:
    """{blank id: spec} from a type-2 payload, tolerating legacy shapes."""
    if not isinstance(payload, dict):
        return {}
    blanks = payload.get("blanks")
    if isinstance(blanks, list):
        out = {}
        for b in blanks:
            if isinstance(b, dict) and "id" in b:
                try:
                    out[int(b["id"])] = b
                except (TypeError, ValueError):
                    continue
        if out:
            return out
    answers = payload.get("answers")
    if isinstance(answers, list) and answers:
        return {i: {"id": i, "answers": [a]} for i, a in enumerate(answers)}
    return {}


def has_inline_data(card_or_payload) -> bool:
    """True when an inline widget can render: template + blank specs."""
    payload = _payload_of(card_or_payload)
    template = payload.get("template")
    if not isinstance(template, str) or not BLANK_RE.search(template):
        return False
    return bool(_blanks_of(payload))


def _width(answers) -> int:
    """Input width from the longest accepted answer, clamped 4..24."""
    try:
        longest = max(len(str(a)) for a in answers)
    except (TypeError, ValueError):
        longest = 0
    return max(4, min(24, longest or 8))


def _input_for(bid: int, spec: dict, values: dict, locked: set) -> str:
    """One blank's input; locked (correct) blanks render readonly.

    Readonly fields still post, so no hidden twin is needed -- the
    retry re-submit carries the same single ``b<id>`` value.
    """
    name = f"b{bid}"
    if bid in locked:
        val = values.get(bid, "")
        if val == "" and isinstance(spec, dict):
            ans = spec.get("answers") or []
            val = ans[0] if ans else ""
        esc = html.escape(str(val), quote=True)
        return (f"<input name='{name}' value='{esc}'"
                f" size='{_width([val])}' readonly"
                f" aria-label='blank {bid} (correct, locked)'>")
    pre = html.escape(str(values.get(bid, "")), quote=True)
    answers = spec.get("answers", []) if isinstance(spec, dict) else []
    return (f"<input name='{name}' size='{_width(answers)}' value='{pre}'"
            f" placeholder='___({bid})' aria-label='blank {bid}'>")


def render_code(template: str, blanks: dict, values=None, locked=()) -> str:
    """Escaped code with an input element at each known ``___(id)`` marker.

    ``values`` ({id: text}) prefills inputs and ``locked`` ({id})
    freezes correct ones for retry flows; both accept str or int ids.
    Markers with no blank spec stay literal text. The template's HTML
    is escaped while substituted inputs stay live.
    """
    norm: dict = {}
    for k, v in (values or {}).items():
        try:
            norm[int(k)] = v
        except (TypeError, ValueError):
            continue
    lock: set = set()
    for k in (locked or ()):
        try:
            lock.add(int(k))
        except (TypeError, ValueError):
            continue
    safe = html.escape(template)

    def _sub(match: re.Match) -> str:
        bid = int(match.group(1))
        if bid not in blanks:
            return match.group(0)
        return _input_for(bid, blanks[bid], norm, lock)

    return BLANK_RE.sub(_sub, safe)


def inline_widget(card_or_payload, conf_html: str = "", values=None,
                  locked=()) -> str:
    """Full etype-2 body with inline inputs; "" when no template data.

    The empty string is the fallback signal: the caller keeps its
    legacy separate-fields body untouched.
    """
    payload = _payload_of(card_or_payload)
    if not has_inline_data(payload):
        return ""
    code = render_code(payload["template"], _blanks_of(payload),
                       values, locked)
    return (f"<pre class='cloze-code'>{code}</pre>"
            f"<div>{conf_html}<button>Check blanks</button></div>")


def enhance(card_or_payload, legacy_body: str, conf_html: str = "",
            values=None, locked=()) -> str:
    """Delegation-thin swap: inline widget when data, else legacy.

    The Due-queue call site is one line --
    ``body = enhance(p, body, _confidence())`` -- and template-less
    cards render byte-identical to today.
    """
    widget = inline_widget(card_or_payload, conf_html, values, locked)
    return widget if widget else legacy_body


_DEMO_TEMPLATE = ("def ___(0)(xs):\n"
                  "    return ___(1)(x for x in xs if ___(2)(x))")

_DEMO_BLANKS = [{"id": 0, "answers": ["total"]},
                {"id": 1, "answers": ["sum"]},
                {"id": 2, "answers": ["valid"]}]


def section_html() -> str:
    """Status-page demo: the same inline widget the Due queue renders."""
    demo = inline_widget({"template": _DEMO_TEMPLATE,
                          "blanks": _DEMO_BLANKS})
    return (f"<h3 id='{STATUS_ANCHOR}'>Inline cloze blanks</h3>"
            "<p>Cloze blanks now sit inside the code they came from -- "
            "type with context in view instead of detached fields below "
            "the card. Same answers, same grading.</p>"
            f"<form method='post' action='#'>{demo}</form>")


def tour_entry() -> dict:
    """Tour stop for the Status-page demo section."""
    return {"id": "inline-cloze-blanks", "kind": "improvement",
            "title": "Inline cloze blanks in code",
            "blurb": ("Cloze blanks render as inputs inside the code "
                      "itself, so you fill them with context in view "
                      "instead of detached fields."),
            "path": "/status", "anchor": STATUS_ANCHOR}
