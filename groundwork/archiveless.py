"""Retired-lesson archive with reason (I-150).

Lessons disappear silently today: regeneration drops cards and
files move on, leaving learners unsure what went where. The
archive names each retired lesson with its reason — a source file
deleted on disk, or a concept whose cards did not survive
regeneration — in one module-page section. Nothing retired keeps
legacy bytes (""). Reasons derive from current state (disk +
card counts), never history. Pure functions plus two
fail-closed probes; stdlib only; never raises.
"""
from __future__ import annotations

import html
import os

STATUS_ANCHOR = "status-b23-archiveless"


def repo_of(module_row) -> str:
    """Repo root off a module row; "" when unknown."""
    try:
        repo = module_row["repo"]
        return str(repo or "")
    except (KeyError, IndexError, TypeError):
        return ""


def reason_for(name, filename, repo_root, has_cards: bool) -> str:
    """Retirement reason or "" when the lesson is live."""
    try:
        if has_cards:
            if not filename or not repo_root:
                return ""
            try:
                if os.path.exists(os.path.join(str(repo_root),
                                               str(filename))):
                    return ""
            except (TypeError, ValueError, OSError):
                return ""
            return "source file deleted"
        if filename and repo_root:
            try:
                if not os.path.exists(os.path.join(str(repo_root),
                                                   str(filename))):
                    return "source file deleted"
            except (TypeError, ValueError, OSError):
                pass
        return "no cards — retired by regeneration"
    except Exception:  # noqa: BLE001 -- reasons must never raise
        return ""


def retired_for(concepts, cards_by_concept=None, repo_root: str = "") -> list:
    """[{name, reason}] for retired lessons; [] when none."""
    try:
        counts = cards_by_concept if isinstance(cards_by_concept, dict) else {}
        out = []
        for row in (concepts or []):
            try:
                cid = row["cid"] if isinstance(row, dict) else row["cid"]
                nm = row["name"] if isinstance(row, dict) else row["name"]
                fn = row["file"] if isinstance(row, dict) else row["file"]
            except (KeyError, IndexError, TypeError):
                continue
            try:
                cards = counts.get(cid, [])
                alive = bool(cards)
            except AttributeError:
                alive = False
            reason = reason_for(nm, fn, repo_root, alive)
            if reason:
                out.append({"name": str(nm), "reason": reason})
        return out
    except Exception:  # noqa: BLE001 -- scan must never raise
        return []


def archive_html(entries) -> str:
    """Archive section; "" when nothing retired (legacy fallback)."""
    try:
        rows = [e for e in (entries or []) if isinstance(e, dict)]
        if not rows:
            return ""
        lis = "".join(
            f"<li>{html.escape(str(r.get('name', 'lesson')))} — "
            f"{html.escape(str(r.get('reason', 'retired')))}</li>"
            for r in rows)
        return (f"<div class='archive'><h3>Retired lessons</h3>"
                f"<ul>{lis}</ul></div>")
    except Exception:  # noqa: BLE001 -- archive must never raise
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Retired lessons "
            "<small>(improvement)</small></h3>"
            "<p>Retired lessons, with reasons — "
            "<code>groundwork/archiveless.py</code> archives lessons "
            "whose source file was deleted or whose cards did not "
            "survive regeneration; live modules render exactly as "
            "before.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Retired lessons</h3>"
                "<p>Archive help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "retired-lessons",
        "kind": "improvement",
        "title": "Retired lessons",
        "blurb": ("Lessons that retire say why — deleted file or "
                  "regenerated cards."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
