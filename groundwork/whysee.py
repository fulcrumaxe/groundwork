"""Shared "Why am I seeing this?" reasons for recommendations (F-138).

Batch 1 shipped due-why tooltips for the Due queue lead card
(cards._due_why): overdue days, memory strength, lapse count.
This module brings the same transparency to the seven surfaces
that showed picks without saying why: the serendipity bonus,
party trick, interview recap track, and re-teach boxes (Due
page), blind spots (Status page), elaboration partners (inside
lesson rendering), and related modules (module pages).
Remediation lifts stay out: queue_remediation reorders without
rendering, so there is no learner-path surface to wire.

Each surface keeps its picker and calls reason_for() with the
live facts it already holds. Every clause traces to a live
scheduling or mastery field (or the pick query's own live
predicate); a missing fact drops its clause instead of inventing
text, and no facts at all renders "" so legacy bytes survive.

Thin call sites, one import plus one call each:

  serendipity:  reason_for("serendipity", {"module": m, "in_due": b})
  preptrack:    reason_for("preptrack", {"mastery": m, "due": d})
  blindspot:    reason_for("blindspot", {"mastery": m, "limit": n})
  elaboration:  elaboration_html(lesson, owned_list, partners)
  related:      reason_for("related", {"same_repo": b, "shared": [...]})
  reteach:      reason_for("reteach", {"first_seen": s, "days_ago": n})
  partytrick:   reason_for("partytrick", {"owned_count": n})

Pure functions, stdlib only, ASCII-only output, never raises.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b26-whysee"

SOURCES = ("serendipity", "preptrack", "blindspot", "elaboration",
           "related", "reteach", "partytrick")

_TOKEN_RE = re.compile(r"[a-z0-9]+")

_STOP = frozenset(
    "a an the to of and or in on for with is are it its as at by be".split())


def _text(value) -> str:
    try:
        if isinstance(value, str):
            return value.strip()
        if value is None:
            return ""
        return str(value).strip()
    except Exception:  # noqa: BLE001 -- coerce never raises
        return ""


def _num(value, default: float = 0.0) -> float:
    try:
        if isinstance(value, bool):
            return default
        got = float(value)
        return got if got == got else default  # NaN falls back
    except (TypeError, ValueError):
        return default
    except Exception:  # noqa: BLE001 -- coerce never raises
        return default


def _has_num(value) -> bool:
    try:
        if isinstance(value, bool) or value is None:
            return False
        return float(value) == float(value)
    except (TypeError, ValueError):
        return False
    except Exception:  # noqa: BLE001 -- check never raises
        return False


def _count(value) -> int | None:
    try:
        if isinstance(value, bool):
            return None
        return int(value)
    except (TypeError, ValueError):
        return None
    except Exception:  # noqa: BLE001 -- coerce never raises
        return None


def _names(value, limit: int) -> list:
    try:
        if isinstance(value, (str, bytes)):
            return []
        return [str(v).strip() for v in list(value or [])
                if str(v).strip()][:max(0, limit)]
    except Exception:  # noqa: BLE001 -- coerce never raises
        return []


def _tokens_of(lesson) -> frozenset:
    try:
        if not isinstance(lesson, dict):
            return frozenset()
        blob = (_text(lesson.get("name")) + " "
                + _text(lesson.get("summary"))).lower()
        return frozenset(t for t in _TOKEN_RE.findall(blob)
                         if t and t not in _STOP)
    except Exception:  # noqa: BLE001 -- tokenize never raises
        return frozenset()


def _serendipity(facts: dict) -> str:
    out = []
    module = _text(facts.get("module"))
    if module:
        out.append(f"in {module}")
    in_due = facts.get("in_due")
    if in_due is False:
        out.append("not in your due queue")
    elif in_due is True:
        out.append("in your due queue")
    return "; ".join(out)


def _preptrack(facts: dict) -> str:
    mastery = _num(facts.get("mastery"), 0.0)
    out = [f"mastery {mastery:.2f}"]
    due = _text(facts.get("due"))
    if due:
        out.append(f"due {due[:10]}")
    return "; ".join(out)


def _blindspot(facts: dict) -> str:
    out = []
    if _has_num(facts.get("mastery")):
        out.append(f"mastery {round(100 * _num(facts.get('mastery'), 0.0))}%")
    limit = _count(facts.get("limit"))
    if limit is not None and limit > 0:
        out.append(f"among your {limit} lowest-mastery concepts")
    return "; ".join(out)


def _elaboration(facts: dict) -> str:
    out = []
    shared = _names(facts.get("shared"), 4)
    if shared:
        out.append("shares: " + ", ".join(shared))
    if facts.get("same_repo") is True:
        out.append("same repo")
    if facts.get("owned") is True:
        out.append("you own it")
    return "; ".join(out)


def _related(facts: dict) -> str:
    out = []
    if facts.get("same_repo") is True:
        out.append("same repo")
    shared = _names(facts.get("shared"), 3)
    if shared:
        out.append("shares: " + ", ".join(shared))
    return "; ".join(out)


def _reteach(facts: dict) -> str:
    out = []
    first = _text(facts.get("first_seen"))
    if first:
        out.append(f"first tried {first[:10]}")
    days = _count(facts.get("days_ago"))
    if days is not None and days >= 0:
        out.append(f"{days} days ago")
    return "; ".join(out)


def _partytrick(facts: dict) -> str:
    n = _count(facts.get("owned_count"))
    if n is not None and n > 0:
        return f"1 of {n} concepts you own"
    return ""


_BUILDERS = {
    "serendipity": _serendipity,
    "preptrack": _preptrack,
    "blindspot": _blindspot,
    "elaboration": _elaboration,
    "related": _related,
    "reteach": _reteach,
    "partytrick": _partytrick,
}


def reason_for(source, facts=None) -> str:
    """One ASCII reason string for a recommendation surface.

    `source` names the surface (see SOURCES); `facts` carries that
    surface's live scheduling/mastery fields. Unknown sources and
    missing facts yield "" (legacy fallback). Never raises.
    """
    try:
        key = _text(source).lower()
        builder = _BUILDERS.get(key)
        if builder is None:
            return ""
        if not isinstance(facts, dict):
            facts = {}
        return builder(facts)
    except Exception:  # noqa: BLE001 -- reasons never raise
        return ""


def reason_html(reason, first: bool = False) -> str:
    """Inline "Why am I seeing this?" note; empty reason renders "".

    The first note on a page may carry id='whysee' (tour target);
    later notes render class-only. Never raises.
    """
    try:
        if not isinstance(reason, str):
            return ""
        text = reason.strip()
        if not text:
            return ""
        tag = " id='whysee'" if first is True else ""
        return (f"<small class='whysee'{tag}>Why am I seeing this? "
                f"{html.escape(text)}</small>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def elaboration_html(lesson, owned, partners, first: bool = False) -> str:
    """Per-partner why-notes for an elaboration drill (lesson rendering).

    `partners` are the live drill partner names; each one found in
    `owned` (mastered siblings) gains a note citing its shared
    tokens with `lesson` plus its owned standing -- both computed
    here from the live dicts, never invented. Unknown partners,
    empty input, or no shared signal renders "". Never raises.
    """
    try:
        if not isinstance(lesson, dict):
            return ""
        if isinstance(partners, (str, bytes)):
            return ""
        try:
            names = [str(p).strip() for p in list(partners or [])
                     if _text(p)]
        except TypeError:
            return ""
        if not names:
            return ""
        try:
            siblings = [o for o in list(owned or [])
                        if isinstance(o, dict)]
        except TypeError:
            return ""
        by_name = {}
        for sib in siblings:
            nm = _text(sib.get("name"))
            if nm and nm not in by_name:
                by_name[nm] = sib
        new_tokens = _tokens_of(lesson)
        bits = []
        shown = 0
        for nm in names[:2]:
            cand = by_name.get(nm)
            if cand is None:
                continue
            shared = sorted(new_tokens & _tokens_of(cand))
            reason = reason_for(
                "elaboration", {"shared": shared, "owned": True})
            if not reason:
                continue
            anchor = first is True and shown == 0
            bits.append(f"<p>{html.escape(nm)}: "
                        f"{reason_html(reason, first=anchor)}</p>")
            shown += 1
        return "".join(bits)
    except Exception:  # noqa: BLE001 -- notes never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; reasons below are computed live."""
    try:
        samples = [
            ("Recap track", reason_for("preptrack", {
                "mastery": 0.2, "due": "2026-09-01T00:00:00Z"})),
            ("Blind spots", reason_for("blindspot", {
                "mastery": 0.12, "limit": 10})),
            ("Elaboration", reason_for("elaboration", {
                "shared": ["route", "flask"], "owned": True})),
            ("Serendipity", reason_for("serendipity", {
                "module": "loops", "in_due": False})),
            ("Party trick", reason_for("partytrick", {"owned_count": 7})),
            ("Related", reason_for("related", {
                "same_repo": True, "shared": ["add"]})),
            ("Re-teach", reason_for("reteach", {
                "first_seen": "2026-08-01T00:00:00Z", "days_ago": 45})),
        ]
        lis = "".join(
            f"<li>{html.escape(label)}: "
            f"{html.escape(text) if text else '(no live facts, no reason)'}</li>"
            for label, text in samples)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Why am I seeing this? "
            "<small>(feature)</small></h3>"
            "<p>Every recommendation carries its live reason. Due cards "
            "already cite overdue days, memory strength, and lapses "
            "(due-why); one shared builder "
            "(<code>groundwork/whysee.py</code> "
            "<code>reason_for()</code>) brings the same transparency to "
            "the recap track, blind spots, elaboration partners, "
            "serendipity, party tricks, related modules, and re-teach "
            "boxes. Missing facts drop their clause, never invent text. "
            "Live samples render below.</p>"
            f"<ul>{lis}</ul>")
    except Exception:  # noqa: BLE001 -- status must always render
        return f"<h3 id='{STATUS_ANCHOR}'>Why am I seeing this?</h3>"


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "why-see-this",
        "kind": "feature",
        "title": "Why am I seeing this?",
        "blurb": ("Recommendations say why: recap track, blind spots, "
                  "elaboration, serendipity, party tricks, related "
                  "modules, re-teach."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
