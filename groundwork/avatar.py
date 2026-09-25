"""Custom duo-tone learner identity, local and playful (F-116).

One stable mark per library: two hues plus a shape derived from
the library path, drawn as a small inline SVG tile. No upload,
no account, no network — the same library always draws the same
friend. It sits beside the History headline so every visit
greets you by color. Pure functions, stdlib hashlib only; never
raises.
"""
from __future__ import annotations

import hashlib
import html

STATUS_ANCHOR = "status-b23-avatar"

SHAPES = ("circle", "square", "diamond", "bars")


def identity_for(key) -> dict:
    """{hue_a, hue_b, shape} stable per key; fail-closed defaults."""
    try:
        raw = str(key or "learner")
    except Exception:  # noqa: BLE001 -- identity must never raise
        raw = "learner"
    try:
        digest = hashlib.sha256(raw.encode("utf-8")).hexdigest()
        hue_a = int(digest[:8], 16) % 360
        hue_b = (hue_a + 40 + int(digest[8:16], 16) % 80) % 360
        shape = SHAPES[int(digest[16:24], 16) % len(SHAPES)]
    except Exception:  # noqa: BLE001 -- identity must never raise
        hue_a, hue_b, shape = 210, 250, SHAPES[0]
    return {"hue_a": hue_a, "hue_b": hue_b, "shape": shape}


def avatar_svg(key) -> str:
    """Duo-tone SVG tile for one key."""
    try:
        spec = identity_for(key)
        mark = ""
        if spec["shape"] == "circle":
            mark = "<circle cx='20' cy='20' r='11'/>"
        elif spec["shape"] == "square":
            mark = "<rect x='9' y='9' width='22' height='22' rx='4'/>"
        elif spec["shape"] == "diamond":
            mark = "<path d='M20 7l13 13-13 13-13-13z'/>"
        else:
            mark = ("<rect x='8' y='10' width='6' height='20' rx='2'/>"
                    "<rect x='17' y='6' width='6' height='24' rx='2'/>"
                    "<rect x='26' y='13' width='6' height='17' rx='2'/>")
        return (
            f"<svg class='avatar' width='40' height='40' viewBox='0 0 40 40' "
            f"role='img' aria-label='Your library mark' "
            f"style='background:hsl({spec['hue_a']},45%,88%)"
            f";fill:hsl({spec['hue_b']},55%,42%)'>{mark}</svg>")
    except Exception:  # noqa: BLE001 -- avatar must never raise
        return ("<svg class='avatar' width='40' height='40' "
                "viewBox='0 0 40 40' role='img' aria-label='Your library "
                "mark'><circle cx='20' cy='20' r='11'/></svg>")


def library_key(db_path: str) -> str:
    """Content-addressed identity key: sorted names + summaries.

    Tmp paths differ per checkout, so the key derives from library
    content instead — same content, same mark, stable goldens.
    """
    try:
        from . import db as dbmod
        con = dbmod.connect(db_path)
        try:
            names = sorted(
                str(r[0] or "") for r in con.execute(
                    "SELECT name FROM concepts").fetchall())
            sums = sorted(
                str(r[0] or "") for r in con.execute(
                    "SELECT task_summary FROM modules").fetchall())
        finally:
            con.close()
        key = "|".join(names + sums)
        return key if key.strip("|") else "learner"
    except Exception:  # noqa: BLE001 -- key must never raise
        return "learner"


def box_html(db_path: str) -> str:
    """Identity box for the History headline."""
    try:
        return (f"<p class='avatar-box' id='library-identity'>"
                f"{avatar_svg(library_key(db_path))} "
                f"<small>Your library mark — same colors every visit, "
                f"private to this library.</small></p>")
    except Exception:  # noqa: BLE001 -- box must never raise
        return ""


def avatar_css() -> str:
    """Raw declarations; parent concats into the head wire."""
    try:
        return (".avatar{border-radius:.5em;vertical-align:middle}"
                ".avatar-box{display:flex;gap:.5em;align-items:center}")
    except Exception:  # noqa: BLE001 -- CSS emitter must never raise
        return ".avatar{border-radius:.5em}"


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Library identity "
            "<small>(feature)</small></h3>"
            "<p>A mark that is yours — "
            "<code>groundwork/avatar.py</code> draws one stable duo-tone "
            "tile per library (local, playful, no account): "
            f"{avatar_svg('groundwork')}</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Library identity</h3>"
                "<p>Identity help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "library-identity",
        "kind": "feature",
        "title": "Library identity",
        "blurb": ("One stable duo-tone mark per library — local, "
                  "playful, no account."),
        "path": "/reviews",
        "anchor": "library-identity",
    }
