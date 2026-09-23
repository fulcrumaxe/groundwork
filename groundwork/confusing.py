"""Per-section "confusing" flags feeding a regeneration queue (I-134).

A learner stuck on one block of an otherwise fine lesson flags exactly
that section; flagged section ids collect into an ordered regen queue so
authors rewrite what the queue names first. Pure helpers over flag maps
plus thin SQLite storage mirroring the clarity-vote pattern (I-114):
one row per flagged section, no schema change to existing tables.

Caller path (lesson generation/rendering, never a Status demo):
``lessons.render_levels`` hangs one toggle per titled block (new
optional ``confusing``/``confusing_cid`` params; absent renders
byte-identical), ``Handler.module_html`` hosts the queue banner, and a
``/concepts/<cid>/confusing`` POST route records/unflags. With no flag
data every helper returns its legacy value (empty queue, "" markup), so
unflagged pages render byte-identical. No web.py logic moves here, just
the renderer calls plus the small POST branch.

Section keys look like ``<concept-id>#<block-slug>`` (e.g.
``ab12:calc.py:add#what-it-does``) so flags survive renames of
surrounding copy and stay scoped to one lesson block.
"""
from __future__ import annotations

import html as htmlmod

from . import db as dbmod

STATUS_ANCHOR = "status-b21-confusing"

MAX_SECTION = 300


def _ensure_table(con) -> None:
    """confusing_flags table; new nullable table, additive only."""
    con.execute(
        "CREATE TABLE IF NOT EXISTS confusing_flags ("
        " section_id TEXT PRIMARY KEY,"
        " flagged_at TEXT NOT NULL DEFAULT"
        " (strftime('%Y-%m-%dT%H:%M:%SZ','now')))")


def _clean_section(section) -> str:
    """Usable section key; "" when blank/hostile. Never raises."""
    try:
        if not isinstance(section, str):
            return ""
        text = section.strip()
        if not text or len(text) > MAX_SECTION or "#" not in text:
            return ""
        return text
    except Exception:  # noqa: BLE001 -- cleaning never raises
        return ""


def normalize_flags(flags) -> dict:
    """Section-id -> True map; missing/hostile input yields {}."""
    try:
        if not isinstance(flags, dict):
            return {}
        return {str(k): True for k, v in flags.items()
                if isinstance(k, str) and k.strip() and v}
    except Exception:  # noqa: BLE001 -- normalizing never raises
        return {}


def is_confusing(section, flags) -> bool:
    """True iff this section id is flagged; False on hostile input."""
    try:
        if not isinstance(section, str) or not section.strip():
            return False
        return section in normalize_flags(flags)
    except Exception:  # noqa: BLE001 -- lookup never raises
        return False


def mark(flags, section) -> dict:
    """New map with `section` flagged; input never mutated."""
    try:
        out = normalize_flags(flags)
        if isinstance(section, str) and section.strip():
            out[section] = True
        return out
    except Exception:  # noqa: BLE001 -- lookup never raises
        return {}


def unmark(flags, section) -> dict:
    """New map with `section` cleared; input never mutated."""
    try:
        out = normalize_flags(flags)
        out.pop(section, None)
        return out
    except Exception:  # noqa: BLE001 -- lookup never raises
        return {}


def section_id(heading, taken=()) -> str:
    """Stable slug for a section heading, deduped with -2/-3 suffixes.

    Same slug rule as lessons.slug so flag keys match page anchors;
    duplicate headings get numeric suffixes so two "Words" blocks keep
    separate flags. Never raises; hostile input yields "section".
    """
    try:
        out = "".join(ch.lower() if ch.isalnum() else "-"
                      for ch in str(heading or ""))
        base = "-".join(filter(None, out.split("-"))) or "section"
    except Exception:  # noqa: BLE001 -- slugging never raises
        base, taken = "section", ()
    try:
        seen = set(taken or ())
    except TypeError:
        seen = set()
    cand, n = base, 2
    while cand in seen:
        cand, n = f"{base}-{n}", n + 1
    return cand


def regen_queue(flags, order=None) -> list:
    """Flagged section ids needing a rewrite, page order when given.

    Without `order` insertion order is kept; with it, flagged ids sort
    by page position and unknown ids trail. Empty/missing flags yield
    [] (legacy: nothing routed). Never raises; non-list input yields [].
    """
    try:
        marked = normalize_flags(flags)
        if not marked:
            return []
        if order is None:
            return list(marked)
        if isinstance(order, str) or not isinstance(order, (list, tuple)):
            return list(marked)
        ranked = [str(s) for s in order
                  if isinstance(s, str) and s in marked]
        rest = [s for s in marked if s not in set(ranked)]
        return ranked + rest
    except Exception:  # noqa: BLE001 -- queue never raises
        return []


def queue_count(flags) -> int:
    """Number of sections awaiting rewrite; 0 on hostile input."""
    try:
        return len(normalize_flags(flags))
    except Exception:  # noqa: BLE001 -- counting never raises
        return 0


def record(db_path: str, section, value) -> dict:
    """Flag (value "1") or unflag (value "0") one section.

    Returns {"section_id": ..., "module_id": ...} or {"error": ...};
    errors stay explicit, never silent. The concept part of the key
    must exist so flags can only name real lessons.
    """
    key = _clean_section(section)
    if not key:
        return {"error": "section must be <concept-id>#<block>"}
    text = str(value).strip() if isinstance(value, str) else str(value)
    if text not in ("0", "1"):
        return {"error": "confusing must be 0 or 1"}
    cid = key.split("#", 1)[0]
    con = dbmod.connect(db_path)
    try:
        _ensure_table(con)
        me = con.execute("SELECT concepts.module_id AS mid FROM concepts"
                         " WHERE id=?", (cid,)).fetchone()
        if me is None:
            return {"error": "unknown concept"}
        if text == "1":
            con.execute("INSERT OR REPLACE INTO"
                        " confusing_flags(section_id) VALUES(?)", (key,))
        else:
            con.execute("DELETE FROM confusing_flags WHERE section_id=?",
                        (key,))
        con.commit()
        return {"section_id": key, "module_id": me["mid"]}
    finally:
        con.close()


def flags_for_module(db_path: str, mid: str) -> dict:
    """{section_id: True} flagged in one module, oldest first."""
    try:
        con = dbmod.connect(db_path)
        try:
            _ensure_table(con)
            rows = con.execute(
                "SELECT section_id FROM confusing_flags"
                " WHERE section_id LIKE ? ORDER BY rowid",
                (f"{mid}:%",)).fetchall()
        finally:
            con.close()
        return {r[0]: True for r in rows}
    except Exception:  # noqa: BLE001 -- render path never raises
        return {}


def flag_button_html(section, flagged: bool = False, cid: str = "",
                     origin: str = "") -> str:
    """Per-section confusing toggle; posts section id + new value.

    Rendered by lessons.render_levels under each titled block with the
    lesson's concept id (for the POST route) and page path (to come
    back to). Never raises; hostile section id yields "".
    """
    try:
        if not isinstance(section, str) or not section.strip():
            return ""
        sid = htmlmod.escape(section, quote=True)
        label = "Confusing (flagged)" if flagged else "Mark confusing"
        val = "0" if flagged else "1"
        cls = "confusing on" if flagged else "confusing"
        action = ""
        if isinstance(cid, str) and cid:
            action = (f" action='/concepts/{htmlmod.escape(cid)}/confusing'")
        back = ""
        if isinstance(origin, str) and origin:
            back = (f"<input type='hidden' name='origin' value='"
                    f"{htmlmod.escape(origin, quote=True)}'>")
        return (f"<form method='post' class='{cls}'{action}>"
                f"<input type='hidden' name='confusing_section'"
                f" value='{sid}'>"
                f"<input type='hidden' name='confusing' value='{val}'>"
                f"{back}<button>{label}</button></form>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def queue_banner_html(flags, base_path: str = "") -> str:
    """Regen-queue banner for Handler.module_html; "" when empty.

    Empty flags return "" so pages without flags render byte-identical
    (legacy no-data fallback). Never raises.
    """
    try:
        queue = regen_queue(flags)
        if not queue:
            return ""
        items = ", ".join(htmlmod.escape(s) for s in queue)
        path = htmlmod.escape(base_path or "", quote=True)
        more = f" <a href='{path}#regen-queue'>details</a>" if path else ""
        return (f"<p class='regen-queue'>"
                f"{len(queue)} section(s) flagged confusing: "
                f"{items}.{more}</p>")
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = queue_banner_html({"worked-example": True})
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Confusing sections "
            "<small>(improvement)</small></h3>"
            "<p>Flag the one section that lost you and only that block "
            "joins the rewrite queue — <code>groundwork/confusing.py</code> "
            "keeps a per-section flag map over the lesson rendering path "
            "(<code>lessons.render_levels</code> toggles, "
            "<code>Handler.module_html</code> banner); pages without flags "
            "render exactly as before.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Confusing sections</h3>"
                "<p>Confusing-flag help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "confusing-sections",
        "kind": "improvement",
        "title": "Flag the confusing section",
        "blurb": ("Mark the one block that lost you and it alone joins "
                  "the rewrite queue."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
