"""Spec pane beside the rebuild editor (I-171).

Type 23 (rebuild-from-spec) prints the spec in the card front and a
bare code editor below it, so the learner scrolls up to re-read the
contract while typing. This renders the same spec and interface
beside the existing editor in a server-side flex split: no new data
(the payload already carries spec and signature), no schema change,
same posting field, same hidden-tests grade. Precedent:
comparesplit.py (side-by-side panes with a byte-identical legacy
fallback). Pure HTML builders; never raises.
"""
from __future__ import annotations

import html
import json
import re

STATUS_ANCHOR = "status-b26-specsplit"
SPEC_TYPE = "23"
MAX_SPEC_CHARS = 2000

_FENCE = re.compile(r"```\w*\n(.*?)```", re.S)
_INTERFACE_LINE = "Keep this interface:"


def _safe_text(value) -> str:
    """Best-effort str(); "" for anything unusable, never raises."""
    try:
        if isinstance(value, str):
            return value
        if value is None:
            return ""
        return str(value)
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return ""


def _front_of(card) -> str:
    """front text for dicts and sqlite Rows; "" when missing."""
    try:
        if isinstance(card, dict):
            return card.get("front", "") or ""
        return card["front"] or ""
    except (KeyError, IndexError, TypeError):
        return ""


def _payload_of(card, payload) -> dict:
    """Payload dict: explicit arg wins, else the card's own; {} if missing."""
    try:
        if isinstance(payload, dict):
            return payload
        if isinstance(card, dict):
            raw = card.get("payload", "{}")
        else:
            try:
                raw = card["payload"]
            except (KeyError, IndexError, TypeError):
                return {}
        if isinstance(raw, dict):
            return raw
        try:
            parsed = json.loads(raw or "{}")
        except ValueError:
            return {}
        return parsed if isinstance(parsed, dict) else {}
    except Exception:  # noqa: BLE001 -- fail closed, never raise
        return {}


def parse_spec(front, payload) -> tuple:
    """(spec, signature) for a rebuild card; ("","") when unusable.

    Payload keys win (gen_rebuild stores both); otherwise the front
    is parsed (prompt first line skipped, interface fence kept).
    """
    try:
        p = payload if isinstance(payload, dict) else {}
        spec = _safe_text(p.get("spec")).strip()
        sig = _safe_text(p.get("signature")).strip()
        if spec or sig:
            return (spec[:MAX_SPEC_CHARS], sig)
        text = _safe_text(front)
        if not text.strip():
            return ("", "")
        m = _FENCE.search(text)
        head = text[:m.start()] if m else text
        if m:
            sig = m.group(1).strip()
        lines = head.splitlines()
        if lines:
            lines = lines[1:]
        lines = [ln for ln in lines if ln.strip() != _INTERFACE_LINE]
        spec = "\n".join(lines).strip()
        if not spec and not sig:
            return ("", "")
        return (spec[:MAX_SPEC_CHARS], sig)
    except Exception:  # noqa: BLE001 -- parse must never raise
        return ("", "")


def spec_pane_html(spec, signature) -> str:
    """Left spec pane; "" when both sides blank/hostile."""
    try:
        s = _safe_text(spec).strip()
        g = _safe_text(signature).strip()
        if not s and not g:
            return ""
        parts = ["<div class='spsplit-spec'><b>Spec</b>"]
        if s:
            parts.append("<div class='spsplit-text'>"
                         + html.escape(s).replace("\n", "<br>") + "</div>")
        if g:
            parts.append("<b>Keep this interface</b><pre>"
                         + html.escape(g) + "</pre>")
        parts.append("</div>")
        return "".join(parts)
    except Exception:  # noqa: BLE001 -- renderer must never raise
        return ""


def split_css() -> str:
    """Raw flex-split declarations (never <style>); head wire joins."""
    return (".spsplit{display:flex;gap:8px;flex-wrap:wrap;}"
            ".spsplit-spec{flex:1;min-width:16em;max-height:22em;"
            "overflow:auto;border:1px solid var(--ink);padding:4px 8px;}"
            ".spsplit-spec pre{margin:4px 0;white-space:pre-wrap;}"
            ".spsplit-text{margin:4px 0;}"
            ".spsplit-edit{flex:1;min-width:16em;}")


def _legacy() -> str:
    """Byte-identical etype-23 body as cards.py renders it today."""
    from . import cards as cardsmod  # lazy: cards.py calls this branch
    from . import codeedit as codeeditmod
    from . import runkey as runkeymod
    return (codeeditmod.editor_html() + runkeymod.hint_html() + "<br>"
            f"{cardsmod._confidence()}" + runkeymod.run_button_html()
            + codeeditmod.editor_js() + runkeymod.exercise_script_js())


def branch_html(card, payload, cid) -> str:
    """Full etype-23 body: spec split + editor, or legacy alone."""
    _ = cid  # call-site shape parity with comparesplit.branch_html
    try:
        from . import codeedit as codeeditmod
        from . import runkey as runkeymod
        from . import cards as cardsmod
        editor = codeeditmod.editor_html()
        tail = (runkeymod.hint_html() + "<br>"
                f"{cardsmod._confidence()}" + runkeymod.run_button_html()
                + codeeditmod.editor_js()
                + runkeymod.exercise_script_js())
        legacy = editor + tail
        spec, sig = parse_spec(_front_of(card),
                               _payload_of(card, payload))
        pane = spec_pane_html(spec, sig)
        if not pane:
            return legacy
        return ("<div class='spsplit'>" + pane
                + "<div class='spsplit-edit'>" + editor + "</div></div>"
                + tail)
    except Exception:  # noqa: BLE001 -- branch must never raise
        try:
            return _legacy()
        except Exception:  # noqa: BLE001 -- legacy must never raise
            return "<textarea name='answer' rows='12' cols='70'></textarea>"


def tour_entry() -> dict:
    """Tour registry entry for the rebuild spec split."""
    return {"id": "rebuild-spec-split", "kind": "improvement",
            "title": "Rebuild spec beside the editor",
            "blurb": "Rebuild spec stays visible beside the editor "
                     "while you type.",
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch26.py."""
    return (f"<h3 id='{STATUS_ANCHOR}'>Rebuild spec beside the editor "
            "<small>(improvement)</small></h3>"
            "<p>Rebuild cards (<code>exercises.gen_rebuild</code>, type 23) "
            "show their spec and interface beside the code editor in a "
            "server-side split from <code>groundwork/specsplit.py</code>: "
            "the payload already carries both strings, so no new data and "
            "no schema change. Same posting field, same hidden-tests "
            "grade; missing specs render the legacy editor alone.</p>"
            + spec_pane_html("Return the sum of two numbers.",
                             "def add(a, b):"))
