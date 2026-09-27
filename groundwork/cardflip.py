"""Flashcard flip between recall and self-rate (I-177).

Type 1 (flashcard) renders the recall textarea stacked over the 0-5
self-rate select in one form (cards.answer_widget, etype "1"). This
module turns those SAME fields -- same names, same order, same grade --
into a two-face flip: the recall face shows first, and a label turns
the card to the self-rate face. Pure CSS, no JS: a nameless checkbox
drives the turn through :checked, so grading (the answer field, 0-5)
and draft preservation (textarea/input[type=text] only) never notice.

Motion fits the shared 300ms budget (FLIP_MS 250ms); a
prefers-reduced-motion block stacks both faces statically with no
transition and no transform. Missing card ids fall back to the legacy
body byte-identical. Pure functions, stdlib only (html), no I/O, no
DB/schema changes, no web.py edits.
"""
from __future__ import annotations

import html

STATUS_ANCHOR = "status-b26-cardflip"

FLIP_MS = 250
BUDGET_MS = 300

_LABELS = ("blank", "wrong", "shaky", "close", "right", "easy")


def duration_ms(value=FLIP_MS) -> int:
    """Flip duration clamped to 0..BUDGET_MS; garbage fails closed."""
    try:
        if isinstance(value, bool):
            return FLIP_MS
        v = int(value)
        if v < 0 or v > BUDGET_MS:
            return FLIP_MS
        return v
    except Exception:  # noqa: BLE001 -- duration must never raise
        return FLIP_MS


def _uid(cid) -> str:
    """Alnum-only checkbox id stem; "" when the id is absent."""
    try:
        if cid is None or isinstance(cid, bool):
            return ""
        return "".join(c for c in str(cid) if c.isalnum())
    except Exception:  # noqa: BLE001 -- coerce must never raise
        return ""


def _card_id(card) -> str:
    """Card id for dicts and sqlite3 Rows; "" when missing."""
    try:
        if isinstance(card, dict):
            return card.get("id", "") or ""
        return card["id"] or ""
    except (KeyError, IndexError, TypeError):
        return ""
    except Exception:  # noqa: BLE001 -- lookup must never raise
        return ""


def is_flashcard(card) -> bool:
    """True only for etype 1 (flashcard); hostile input is False."""
    try:
        if isinstance(card, dict):
            etype = card.get("exercise_type", "")
        else:
            etype = card["exercise_type"]
        return str(etype) == "1"
    except (KeyError, IndexError, TypeError):
        return False
    except Exception:  # noqa: BLE001 -- check must never raise
        return False


def legacy_body() -> str:
    """Pre-flip etype-1 body, byte-identical (the absent-data path)."""
    from . import cards as cardsmod
    opts = "".join(f"<option value='{i}'>{i} — {w}</option>"
                   for i, w in enumerate(_LABELS))
    return (f"<label>Say it back in your own words first "
            f"(optional, this is the recall):<br>"
            f"<textarea name='recall' rows='3' cols='60'></textarea></label><br>"
            f"<label>Then rate how well you recalled it: "
            f"<select name='answer'>{opts}</select></label> "
            f"{cardsmod._confidence()}<button>Submit rating</button>")


def flip_css() -> str:
    """Raw flip declarations (never <style>); parent joins the head wire."""
    try:
        ms = duration_ms()
    except Exception:  # noqa: BLE001 -- CSS must never raise
        ms = FLIP_MS
    try:
        return (
            ".cflip{perspective:60rem}"
            ".cflip-toggle{position:absolute;opacity:0;width:1em;height:1em}"
            f".cflip-inner{{display:grid;transition:transform {ms}ms ease;"
            "transform-style:preserve-3d}"
            ".cflip-toggle:checked~.cflip-inner{transform:rotateY(180deg)}"
            ".cflip-face{grid-area:1/1;backface-visibility:hidden;min-width:0}"
            ".cflip-back{transform:rotateY(180deg)}"
            ".cflip-go{display:inline-block;margin-top:.5rem;"
            "text-decoration:underline;cursor:pointer}"
            "@media (prefers-reduced-motion:reduce){"
            ".cflip{perspective:none}"
            ".cflip-inner{display:block;transition:none;transform:none}"
            ".cflip-toggle:checked~.cflip-inner{transform:none}"
            ".cflip-face{backface-visibility:visible}"
            ".cflip-back{transform:none}"
            ".cflip-toggle,.cflip-go{display:none}}"
        )
    except Exception:  # noqa: BLE001 -- CSS must never raise
        return ".cflip-inner{display:block}"


def branch_html(card, cid=None) -> str:
    """Full etype-1 body: flip faces, or legacy bytes when id is absent."""
    try:
        uid = _uid(cid if cid is not None else _card_id(card))
        if not uid:
            return legacy_body()
        from . import cards as cardsmod
        opts = "".join(f"<option value='{i}'>{i} — {w}</option>"
                       for i, w in enumerate(_LABELS))
        recall = ("<label>Say it back in your own words first "
                  "(optional, this is the recall):<br>"
                  "<textarea name='recall' rows='3' cols='60'></textarea></label>")
        rate = (f"<label>Then rate how well you recalled it: "
                f"<select name='answer'>{opts}</select></label> "
                f"{cardsmod._confidence()}<button>Submit rating</button>")
        tag = html.escape(uid, quote=True)
        return (
            "<div class='cflip'>"
            f"<input type='checkbox' class='cflip-toggle' id='cf{tag}'>"
            "<div class='cflip-inner'>"
            f"<div class='cflip-face cflip-front'>{recall}<br>"
            f"<label class='cflip-go' for='cf{tag}'>Rate yourself -></label></div>"
            f"<div class='cflip-face cflip-back'>{rate}<br>"
            f"<label class='cflip-go' for='cf{tag}'>Back to recall</label></div>"
            "</div></div>"
        )
    except Exception:  # noqa: BLE001 -- branch must never raise
        try:
            return legacy_body()
        except Exception:  # noqa: BLE001 -- legacy must never raise
            return "<textarea name='recall' rows='3' cols='60'></textarea>"


def tour_entry() -> dict:
    """Tour registry entry for the flashcard flip."""
    return {"id": "flashcard-flip", "kind": "improvement",
            "title": "Flashcard flip",
            "blurb": "Flashcards turn from recall to self-rate like a card in your hand -- still and stacked for reduced-motion users.",
            "path": "/status", "anchor": STATUS_ANCHOR}


def section_html() -> str:
    """Anchored status subsection; joined by the parent batch module."""
    try:
        demo = branch_html({"id": "demo1", "exercise_type": 1}, "demo1")
    except Exception:  # noqa: BLE001 -- status must never raise
        demo = ""
    return (f"<h3 id='{STATUS_ANCHOR}'>Flashcard flip <small>(improvement)</small></h3>"
            "<p>Flashcards (type 1, <code>cards.answer_widget</code>) turn from "
            "recall to self-rate: the same textarea and 0-5 select ride two "
            "faces of one card, and a label flips between them with pure CSS "
            "(a nameless <code>:checked</code> checkbox -- no JS, no grading "
            "change, same posted fields in the same order). The turn runs "
            f"{FLIP_MS}ms inside the shared 300ms motion budget, and a "
            "<code>prefers-reduced-motion</code> block stacks both faces "
            "statically. Missing card ids render the legacy body "
            "byte-identical. <code>groundwork/cardflip.py</code> provides "
            "<code>branch_html()</code> (the etype-1 branch) and "
            "<code>flip_css()</code> (raw declarations for the head wire).</p>"
            + demo)
