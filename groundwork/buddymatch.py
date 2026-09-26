"""Buddy matching by repo overlap (F-126): opt-in, local only.

Single-learner app, so there are no real peers to directory: matching is
a pure local overlap computation. The module page knows its own
footprint (its repo plus its concept names); the friend's footprint
arrives as plain query data the learner pastes into the opt-in form
(their repos + concept names, comma-separated). There is no network,
no stored directory, no second-user protocol, and nothing is
fabricated: scores compare user-supplied sets only. No opt-in or no
overlap renders "" so the page keeps its legacy bytes.

Composes instead of duplicating: names are scrubbed with
buddyview.clean_name, and the overlap signals are related.py's two
signals (same repo, shared concept names) scored over in-memory sets.
Pure functions, stdlib html only; never raises. The caller is
``Handler.module_html`` beside the buddy panes.
"""
from __future__ import annotations

import html

from .buddyview import clean_name

STATUS_ANCHOR = "status-b24-buddymatch"

MAX_PROFILES = 10
MAX_ITEMS = 8
MAX_SHARED_SHOWN = 5
MIN_SCORE = 0.01


def _str_set(value, cap: int = MAX_ITEMS) -> set:
    """Scrubbed set of short strings; hostile input gives set().

    Bare strings split on commas, so one pasted "calc, web" field
    and a ["calc, web"] query list mean the same thing.
    """
    try:
        if not isinstance(value, (list, tuple, set, frozenset)):
            if isinstance(value, str):
                value = [v for v in value.split(",")]
            else:
                return set()
        out = set()
        for v in value:
            if not isinstance(v, str):
                continue
            s = v.strip()[:80]
            if s:
                out.add(s)
            if len(out) >= cap:
                break
        return out
    except Exception:  # noqa: BLE001 -- sets must never raise
        return set()


def clean_profile(prof) -> dict:
    """Scrubbed {name, repos, concepts}; hostile input gives empties."""
    try:
        if not isinstance(prof, dict):
            return {"name": "", "repos": set(), "concepts": set()}
        return {
            "name": clean_name(prof.get("name")),
            "repos": _str_set(prof.get("repos")),
            "concepts": _str_set(prof.get("concepts")),
        }
    except Exception:  # noqa: BLE001 -- profiles must never raise
        return {"name": "", "repos": set(), "concepts": set()}


def jaccard(first: set, second: set) -> float:
    """Jaccard similarity in [0.0, 1.0]; empty union scores 0.0."""
    try:
        a, b = set(first or set()), set(second or set())
        if not (a | b):
            return 0.0
        return len(a & b) / len(a | b)
    except Exception:  # noqa: BLE001 -- scoring must never raise
        return 0.0


def overlap_score(me: dict, other: dict,
                  w_repo: float = 0.5, w_concept: float = 0.5) -> float:
    """Weighted repo/concept overlap in [0.0, 1.0]; hostile input is 0.0."""
    try:
        mine, theirs = clean_profile(me), clean_profile(other)
        score = (w_repo * jaccard(mine["repos"], theirs["repos"])
                 + w_concept * jaccard(mine["concepts"], theirs["concepts"]))
        return min(1.0, max(0.0, float(score)))
    except Exception:  # noqa: BLE001 -- scoring must never raise
        return 0.0


def match_buddies(me, profiles, limit: int = 5,
                  min_score: float = MIN_SCORE) -> list:
    """Ranked [(name, score, shared_repos, shared_concepts)]; never raises.

    Sorted by score descending, then name. Skips the learner's own name,
    nameless profiles, and scores below min_score.
    """
    try:
        mine = clean_profile(me)
        if not isinstance(profiles, (list, tuple)):
            return []
        ranked = []
        for prof in profiles[:MAX_PROFILES]:
            theirs = clean_profile(prof)
            if not theirs["name"] or theirs["name"] == mine["name"]:
                continue
            score = overlap_score(mine, theirs)
            if score < min_score:
                continue
            ranked.append((
                theirs["name"], round(score, 3),
                sorted((mine["repos"] & theirs["repos"]))[:MAX_SHARED_SHOWN],
                sorted((mine["concepts"] & theirs["concepts"]))[:MAX_SHARED_SHOWN],
            ))
        ranked.sort(key=lambda r: (-r[1], r[0]))
        try:
            return ranked[:max(0, int(limit))]
        except (TypeError, ValueError):
            return ranked[:5]
    except Exception:  # noqa: BLE001 -- matching must never raise
        return []


def match_html(me, profiles, opt_in: bool = False, limit: int = 5) -> str:
    """Ranked overlap list; "" unless opted in with at least one match."""
    try:
        if not opt_in:
            return ""
        matches = match_buddies(me, profiles, limit)
        if not matches:
            return ""
        rows = []
        for name, score, repos, concepts in matches:
            shared = ", ".join([*repos, *concepts][:MAX_SHARED_SHOWN])
            note = (f" <small>({html.escape(shared)})</small>"
                    if (repos or concepts) else "")
            rows.append(f"<li>{html.escape(name)} — {score:.0%}{note}</li>")
        items = "".join(rows)
        return (f"<div class='buddy-match'><h4>Buddies by repo overlap</h4>"
                f"<ol>{items}</ol></div>")
    except Exception:  # noqa: BLE001 -- view must never raise
        return ""


def entry_html(base: str) -> str:
    """Opt-in form (GET ?buddymatch=1); always safe to render.

    The friend's footprint is pasted here (their repos + concept
    names, comma-separated) so scoring compares user-supplied sets.
    """
    try:
        action = html.escape(str(base or "/modules"), quote=True)
        return (
            f"<form class='buddy-match-entry' method='get' action='{action}'>"
            "<label><input type='checkbox' name='buddymatch' value='1'> "
            "Match study buddies by repo overlap (local only)</label><br>"
            "<label>Friend's repos "
            "<input name='bmatch_repos' maxlength='200' "
            "placeholder='calc, web'></label> "
            "<label>Friend's concepts "
            "<input name='bmatch_concepts' maxlength='200' "
            "placeholder='add, loops'></label> "
            "<button type='submit'>Find buddies</button></form>")
    except Exception:  # noqa: BLE001 -- entry must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch24.py."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Buddy matching by repo overlap "
            "<small>(feature)</small></h3>"
            "<p>Opt-in local matching — "
            "<code>groundwork/buddymatch.py</code> ranks buddy profiles by "
            "shared repos and concept names, all in memory (no network, no "
            "stored directory, nothing fabricated: the friend's footprint "
            "is pasted into the opt-in form); opted out or with no overlap "
            "it renders nothing and the page keeps its legacy bytes.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Buddy matching</h3>"
                "<p>Buddy matching help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "buddy-match",
        "kind": "feature",
        "title": "Buddy matching by repo overlap",
        "blurb": ("Opt in to find overlapping repos — local only, no directory."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
