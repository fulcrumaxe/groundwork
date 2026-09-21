"""Elaboration drills (F-59): connect a new concept to two you already own.

Library helper, not a new graded exercise type — no pipeline,
exercises, or grading changes. The parent renders one drill on the
status/batch page; nothing touches the DB or the schema.

Relatedness mirrors groundwork/related.py (same repo or shared
concept tokens) and the adjacency idea in groundwork/serendipity.py
(nearby work first). Owned-concept dicts reuse the vocabulary from
groundwork/ownership.py (``name`` plus optional ``repo``/``summary``)
read-only — this module never queries ownership itself.

Pure functions, stdlib only, no groundwork imports, no I/O.
Every public helper fails closed and never raises.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b12-elaboration"

REPO_BONUS = 2

_STOP = frozenset({
    "a", "an", "the", "to", "of", "and", "or", "in", "on", "for",
    "with", "is", "are", "it", "its", "as", "at", "by", "be",
})

_TOKEN_RE = re.compile(r"[a-z0-9]+")


def _text(value) -> str:
    try:
        if value is None:
            return ""
        if isinstance(value, str):
            return value
        if isinstance(value, (list, tuple)):
            return " ".join(_text(v) for v in value)
        if isinstance(value, dict):
            return " ".join(_text(v) for v in value.values())
        return str(value)
    except Exception:  # noqa: BLE001 -- text coerce never raises
        return ""


def _name(concept) -> str:
    try:
        if isinstance(concept, dict):
            return str(concept.get("name") or "").strip()
        return ""
    except Exception:  # noqa: BLE001 -- name lookup never raises
        return ""


def _repo(concept) -> str:
    try:
        if isinstance(concept, dict):
            return str(concept.get("repo") or "").strip()
        return ""
    except Exception:  # noqa: BLE001 -- repo lookup never raises
        return ""


def _tokens(concept) -> frozenset:
    try:
        blob = " ".join([
            _text(concept.get("name") if isinstance(concept, dict) else ""),
            _text(concept.get("summary") if isinstance(concept, dict) else ""),
        ]).lower()
        return frozenset(
            t for t in _TOKEN_RE.findall(blob) if t and t not in _STOP)
    except Exception:  # noqa: BLE001 -- tokenize never raises
        return frozenset()


def _score(new_tokens: frozenset, new_repo: str, cand) -> tuple:
    """(score, name): shared tokens + repo bonus; never raises."""
    try:
        cand_tokens = _tokens(cand)
        shared = new_tokens & cand_tokens
        bonus = 0
        try:
            if new_repo and _repo(cand) and _repo(cand) == new_repo:
                bonus = REPO_BONUS
        except Exception:  # noqa: BLE001 -- repo compare never raises
            bonus = 0
        return (len(shared) + bonus, _name(cand), sorted(shared))
    except Exception:  # noqa: BLE001 -- scoring never raises
        return (0, "", [])


def elaboration_drill(new_concept: dict, owned: list[dict]) -> dict:
    """Pick the two owned concepts closest to ``new_concept``.

    Score = shared name/summary tokens + REPO_BONUS on same repo
    (same-repo/shared-concept relatedness, cf. related.py).
    Deterministic: ties break alphabetically by partner name.
    Fewer than two nameable owned concepts -> ``partners == []``
    with a study-first prompt/bridge. Never raises.
    """
    try:
        concept = _name(new_concept) or "this concept"
        items = []
        try:
            owned = list(owned) if isinstance(owned, (list, tuple)) else []
        except Exception:  # noqa: BLE001 -- bad owned fails closed
            owned = []
        for cand in owned:
            nm = _name(cand)
            if nm and nm != concept:
                items.append(cand)
        if len(items) < 2:
            note = (f"{concept} is new — study two owned concepts first, "
                    "then return here to connect them.")
            return {"concept": concept, "partners": [],
                    "prompt": note, "bridge": note}
        new_tokens = _tokens(new_concept)
        new_repo = _repo(new_concept)
        ranked = []
        for cand in items:
            score, nm, shared = _score(new_tokens, new_repo, cand)
            ranked.append((-score, nm.lower(), nm, score, sorted(shared)))
        ranked.sort()
        top = ranked[:2]
        partners = [t[2] for t in top]
        bits = []
        for neg, _low, nm, score, shared in top:
            if shared:
                bits.append(f"{nm} (shares: {', '.join(shared[:4])})")
            elif new_repo and _repo(
                    next(c for c in items if _name(c) == nm)) == new_repo:
                bits.append(f"{nm} (same repo)")
            else:
                bits.append(nm)
        prompt = (f"Explain {concept} from scratch, then connect it: "
                  f"how is it like {partners[0]}, and how is it like "
                  f"{partners[1]}? Name one difference from each.")
        bridge = f"Bridge {concept} via {' + '.join(bits)}."
        return {"concept": concept, "partners": partners,
                "prompt": prompt, "bridge": bridge}
    except Exception:  # noqa: BLE001 -- drill never raises
        try:
            concept = _name(new_concept) or "this concept"
        except Exception:  # noqa: BLE001 -- fallback never raises
            concept = "this concept"
        note = (f"{concept} is new — study two owned concepts first, "
                "then return here to connect them.")
        return {"concept": concept, "partners": [],
                "prompt": note, "bridge": note}


def drill_html(drill) -> str:
    """Escaped drill markup; bad input renders an empty state."""
    try:
        if not isinstance(drill, dict):
            return "<p>No elaboration drill yet.</p>"
        concept = html.escape(str(drill.get("concept") or "this concept"))
        partners = drill.get("partners") or []
        if not isinstance(partners, list) or not partners:
            prompt = html.escape(str(drill.get("prompt") or
                                     "Study two owned concepts first."))
            return (f"<article><h4>{concept} — elaboration drill</h4>"
                    f"<p>{prompt}</p></article>")
        lis = "".join(f"<li>{html.escape(str(p))}</li>"
                      for p in partners[:2])
        prompt = html.escape(str(drill.get("prompt") or ""))
        bridge = html.escape(str(drill.get("bridge") or ""))
        return (f"<article><h4>{concept} — elaboration drill</h4>"
                f"<p>{prompt}</p><ul>{lis}</ul><p>{bridge}</p></article>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return "<p>No elaboration drill yet.</p>"


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Elaboration drills <small>(feature)</small></h3>"
        "<p>Connect a new concept to two you already own — the drill "
        "picks the two owned concepts sharing the most name/summary "
        "tokens (same repo breaks ties), then asks how the new idea is "
        "like each and how it differs. Library only, not a graded "
        "exercise type: <code>groundwork/elaboration.py</code> provides "
        "<code>elaboration_drill()</code> (fail-closed, never raises) "
        "and escaped <code>drill_html()</code>.</p>"
    )


def tour_entry() -> dict:
    """Feature-tour registry entry (appended to tour.ENTRIES by parent)."""
    return {"id": "elaboration-drills", "kind": "feature",
            "title": "Elaboration drills",
            "blurb": "Connect a new concept to two you already own — shared tokens pick the partners.",
            "path": "/status", "anchor": "status-b12-elaboration"}
