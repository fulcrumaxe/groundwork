"""One-click practice-similar variants for failed cards (I-191).

Failing a card whose prompt order is data (shuffled choice buttons,
Parsons/call-path lines, match columns) mints one sibling row: same
concept, same exercise type, same front/back, reshuffled payload, due
immediately. The result page links straight to it, so one click starts
a fresh attempt at the same skill instead of a dead end.

Why a reshuffle is a real variant: generators seed their shuffle from
the exercise id (exercises.py uses random.Random(hash(ex_id) ...)), so
a new id means a new order; grading compares against stored
answer/solution text and answer_widget renders these lists in payload
order (cards.py), so the sibling grades identically with no pipeline
run, no schema change, and no new exercise type. Cards with no order
in their payload (flashcards, cloze, explain, compare's baked A/B
front) get no button: fail-closed to today's result page.

eligible/variant_payload/link_html are pure; mint_variant takes the
caller's open connection and never commits; offer_html wraps both for
MCPServer.submit_review. Stdlib only.
"""
from __future__ import annotations

import hashlib
import json
import random
from datetime import datetime, timezone

from . import cardlinks as cardlinksmod

STATUS_ANCHOR = "status-b28-similar"

# Grading-invariant under a payload reshuffle: graders compare the
# submission against stored answer/solution text, never positions.
# Type 22 is excluded: its A/B answer is baked into the front text.
CHOICE_TYPES = frozenset({"3", "4", "7", "8", "16", "18"})
ORDER_TYPES = frozenset({"10", "11"})
MATCH_TYPES = frozenset({"30"})
VARIANT_TYPES = CHOICE_TYPES | ORDER_TYPES | MATCH_TYPES

SEP = "~sim"
MAX_SIBLINGS = 99


def _rng(seed_text: str):
    """Stable shuffle source mirroring the generators' seeded pattern."""
    digest = hashlib.sha256(str(seed_text).encode("utf-8")).digest()
    return random.Random(int.from_bytes(digest[:8], "big"))


def _permute(items: list, rng) -> list | None:
    """A reorder of items that differs from items; None if impossible."""
    base = list(items)
    if len(base) < 2:
        return None
    for _ in range(8):
        cand = base[:]
        rng.shuffle(cand)
        if cand != base:
            return cand
    for i in range(len(base) - 1):
        if base[i] != base[i + 1]:
            cand = base[:]
            cand[i], cand[i + 1] = cand[i + 1], cand[i]
            return cand
    return None


def _match_key(pairs: list, left: list, right: list) -> dict:
    """Fresh index->letter key for reshuffled match columns."""
    key = {}
    for i, a in enumerate(left):
        b = next((bb for aa, bb in pairs if aa == a), None)
        key[str(i)] = chr(ord("A") + right.index(b)) if b in right else "?"
    return key


def eligible(exercise_type, payload) -> bool:
    """True when a genuine reshuffled variant exists for this card."""
    try:
        t = str(exercise_type)
        p = payload if isinstance(payload, dict) else {}
        if t in CHOICE_TYPES:
            ch = p.get("choices")
            return (isinstance(ch, list) and len(
                {c for c in ch if isinstance(c, str) and c.strip()}) >= 2)
        if t in ORDER_TYPES:
            lines, sol = p.get("lines"), p.get("solution")
            return (isinstance(lines, list) and len(lines) >= 2
                    and isinstance(sol, list) and len(sol) >= 1)
        if t in MATCH_TYPES:
            pairs, left, right = p.get("pairs"), p.get("left"), p.get("right")
            return (isinstance(pairs, list) and len(pairs) >= 2
                    and isinstance(left, list) and len(left) >= 2
                    and isinstance(right, list) and len(right) >= 2)
        return False
    except Exception:  # noqa: BLE001 -- eligibility never raises
        return False


def variant_payload(exercise_type, payload, seed_text) -> dict | None:
    """Reshuffled payload copy; None when no genuine variant exists."""
    try:
        t = str(exercise_type)
        if not isinstance(payload, dict):
            return None
        rng = _rng(str(seed_text))
        if t in CHOICE_TYPES:
            new = _permute(payload.get("choices") or [], rng)
            if new is None:
                return None
            out = dict(payload)
            out["choices"] = new
            return out
        if t in ORDER_TYPES:
            new = _permute(payload.get("lines") or [], rng)
            if new is None or not payload.get("solution"):
                return None
            out = dict(payload)
            out["lines"] = new
            return out
        if t in MATCH_TYPES:
            pairs = payload.get("pairs") or []
            new_left = _permute(payload.get("left") or [], rng)
            new_right = _permute(payload.get("right") or [], rng)
            if new_left is None or new_right is None or len(pairs) < 2:
                return None
            out = dict(payload)
            out["left"] = new_left
            out["right"] = new_right
            out["key"] = _match_key(pairs, new_left, new_right)
            return out
        return None
    except Exception:  # noqa: BLE001 -- variants never raise
        return None


def variant_id(card_id: str, n: int) -> str:
    """Sibling id for the nth variant of one card."""
    return f"{card_id}{SEP}{n}"


def existing_variants(con, card_id: str) -> list:
    """Variant ids already minted for one card, oldest first."""
    try:
        esc = str(card_id).replace("\\", "\\\\").replace(
            "%", "\\%").replace("_", "\\_")
        rows = con.execute(
            "SELECT id FROM cards WHERE id LIKE ? ESCAPE '\\' ORDER BY id",
            (esc + SEP + "%",)).fetchall()
        return [r[0] for r in rows]
    except Exception:  # noqa: BLE001 -- lookup never raises
        return []


def outstanding_variant(con, card_id: str):
    """Newest unreviewed variant id, else None (at most one live)."""
    try:
        for vid in existing_variants(con, card_id):
            row = con.execute(
                "SELECT 1 FROM reviews WHERE card_id=? LIMIT 1",
                (vid,)).fetchone()
            if row is None:
                return vid
        return None
    except Exception:  # noqa: BLE001 -- lookup never raises
        return None


def _utcnow_iso() -> str:
    try:
        return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    except Exception:  # noqa: BLE001 -- clock never raises
        return "2000-01-01T00:00:00Z"


def mint_variant(con, card, now_iso: str | None = None):
    """Insert (or reuse) the live sibling row; None when ineligible.

    Same concept, type, front, and back; reshuffled payload; due now so
    the Due queue and module page serve it immediately. Never commits:
    the caller owns the transaction. Never raises.
    """
    try:
        cid = str(card["id"] or "")
        concept = str(card["concept_id"] or "")
        etype = str(card["exercise_type"] or "")
        front = str(card["front"] or "")
        back = str(card["back"] or "")
        raw = card["payload"]
        payload = raw if isinstance(raw, dict) else json.loads(raw or "{}")
        if not cid or not concept or not isinstance(payload, dict):
            return None
        if not eligible(etype, payload):
            return None
        live = outstanding_variant(con, cid)
        if live:
            return live
        taken = set(existing_variants(con, cid))
        vid = None
        for n in range(len(taken) + 1, MAX_SIBLINGS + 1):
            cand = variant_id(cid, n)
            if cand in taken:
                continue
            row = con.execute(
                "SELECT 1 FROM cards WHERE id=?", (cand,)).fetchone()
            if row is None:
                vid = cand
                break
        if vid is None:
            return None
        vp = variant_payload(etype, payload, vid)
        if vp is None:
            return None
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back,"
            " payload, due) VALUES(?,?,?,?,?,?,?)",
            (vid, concept, etype, front, back, json.dumps(vp),
             now_iso or _utcnow_iso()))
        return vid
    except Exception:  # noqa: BLE001 -- minting never raises
        return None


def link_html(module_id: str, variant_id_: str) -> str:
    """One-click button to the variant card; "" when unusable."""
    try:
        url = cardlinksmod.card_url(module_id, variant_id_) if module_id else ""
        if not url:
            url = "/due"
        return (f"<p><a class='btn' href='{url}'>Practice a similar card</a> "
                "<small>Same concept, same format, new shuffle - "
                "due now.</small></p>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def offer_html(con, card, passed: bool, module_id: str = "",
               now_iso: str | None = None) -> str:
    """Result-page offer: "" on pass/ineligible, else the button."""
    try:
        if passed:
            return ""
        vid = mint_variant(con, card, now_iso=now_iso)
        if not vid:
            return ""
        return link_html(module_id, vid)
    except Exception:  # noqa: BLE001 -- offers never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the Batch 28 home."""
    try:
        sample = link_html("demo", variant_id("demo:ex001", 1))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Practice a similar card "
            "<small>(improvement)</small></h3>"
            "<p>Fail a shuffle-based card (choice buttons, Parsons or "
            "call-path lines, match columns) and the result page offers "
            "one click to a freshly minted sibling: "
            "<code>groundwork/similar.py</code> inserts the same concept, "
            "type, front, and back with a reshuffled payload due now, so "
            "grading is identical with no schema change and no new "
            "exercise type. At most one sibling stays unreviewed per "
            "card; passes and order-free cards render exactly as before. "
            "A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Practice a similar card</h3>"
                "<p>Status help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "practice-similar",
        "kind": "improvement",
        "title": "Practice a similar card",
        "blurb": ("Fail a shuffle-based card and one click deals a fresh "
                  "sibling: same concept, same format, new order, due now."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
