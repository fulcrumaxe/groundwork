"""Per-element motivational opt-outs (F-139): granular toggles, no schema.

Nineteen motivational sections across the Due queue and the History
page each hide on their own: celebrations, gardens, bests, badges,
mascots, and the rest. State rides the URL as
``?optout=garden,bests`` (comma-separated keys, unknown keys dropped),
persisted across navigation by the ``_send`` carry-over pass exactly
like ``?level=`` (I-4): bookmarkable, per-browser, no cookies (the app
reads none), no database columns. An absent or empty ``optout``
renders every element exactly as before.

Pure functions, stdlib only. Callers: ``history.history_html``
(query already in scope) and ``web.Handler.due_html`` (one threaded
``optout`` string) wrap each motivational join entry in
``html if optout.show(opt, key) else ""``.
"""
from __future__ import annotations

import html
import re
from urllib.parse import parse_qs

STATUS_ANCHOR = "status-b26-optout"

BOX_ANCHOR = "optout-toggles"

DUE_PAGE = "/due"

HISTORY_PAGE = "/reviews"

# (key, home page, label, live marker): every key gates one real
# render call on a live learner page. Markers are the section anchors
# (weekdigest has none, so its heading text stands in).
ELEMENTS: tuple = (
    ("comeback", DUE_PAGE, "Comeback box", "id='comeback'"),
    ("peak", DUE_PAGE, "Peak-recall banner", "id='peaktime'"),
    ("mascot", DUE_PAGE, "Mascot line", "id='mascot'"),
    ("serendipity", DUE_PAGE, "Serendipity card", "id='serendipity'"),
    ("party", DUE_PAGE, "Party trick", "id='partytrick'"),
    ("hero", DUE_PAGE, "Done hero", "id='done-hero'"),
    ("rest", DUE_PAGE, "Rest-day note", "id='rest-day'"),
    ("garden", HISTORY_PAGE, "Knowledge garden", "id='knowledge-garden'"),
    ("rings", HISTORY_PAGE, "Growth rings", "id='growth-rings-head'"),
    ("milestones", HISTORY_PAGE, "Milestone moments", "id='milestones'"),
    ("bests", HISTORY_PAGE, "Personal bests", "id='bests'"),
    ("pledge", HISTORY_PAGE, "Anti-streak pledge", "id='antistreak'"),
    ("showcase", HISTORY_PAGE, "Badge showcase", "id='showcase'"),
    ("unlocks", HISTORY_PAGE, "Theme unlocks", "id='theme-unlocks'"),
    ("share", HISTORY_PAGE, "Milestone share-cards", "id='share-cards'"),
    ("weekdigest", HISTORY_PAGE, "Weekly digest", "Weekly lesson digest"),
    ("challenge", HISTORY_PAGE, "Team challenges", "id='teamchallenge'"),
    ("season", HISTORY_PAGE, "Seasonal event", "id='seasonal-event'"),
    ("anniversary", HISTORY_PAGE, "Anniversary recap", "id='anniversary'"),
)

KEYS = frozenset(k for k, _p, _l, _m in ELEMENTS)

_HREF_RE = re.compile(r"""href=(['"])(.*?)\1""")

_SKIP_PREFIXES = ("#", "http://", "https://", "//", "mailto:",
                  "data:", "javascript:", "tel:")


def _split_values(values) -> set:
    """Known keys from raw values; unknown keys dropped."""
    out = set()
    for v in values:
        for bit in str(v).split(","):
            key = bit.strip().lower()
            if key in KEYS:
                out.add(key)
    return out


def parse(current) -> frozenset:
    """Opted-out keys from a query, string, or set; never raises.

    Accepts a parse_qs dict (``{"optout": [...]}``), a canonical or raw
    query string, a list/tuple/set of values, or None. Anything
    unparseable yields the empty set (show everything).
    """
    try:
        if current is None:
            return frozenset()
        if isinstance(current, (set, frozenset)):
            return frozenset(k.strip().lower() for k in current
                             if isinstance(k, str)
                             and k.strip().lower() in KEYS)
        if isinstance(current, dict):
            vals = current.get("optout", [])
            if isinstance(vals, str):
                vals = [vals]
            return frozenset(_split_values(vals))
        if isinstance(current, (list, tuple)):
            return frozenset(_split_values(current))
        if isinstance(current, str):
            if "=" in current:
                return parse(parse_qs(current, keep_blank_values=True))
            return frozenset(_split_values([current]))
    except Exception:  # noqa: BLE001 -- gates must never break pages
        return frozenset()
    return frozenset()


def normalize(current) -> str:
    """Canonical ``?optout=`` value: sorted known keys, "" when empty."""
    return ",".join(sorted(parse(current)))


def show(current, key: str) -> bool:
    """True unless `key` is opted out; unknown keys always show."""
    return key not in parse(current)


def toggle(current, key: str) -> str:
    """Canonical value with `key` flipped; unknown keys are a no-op."""
    if key not in KEYS:
        return normalize(current)
    off = set(parse(current))
    if key in off:
        off.discard(key)
    else:
        off.add(key)
    return ",".join(sorted(off))


def elements_for(page) -> tuple:
    """ELEMENTS rows whose home page is `page` (default Due)."""
    home = page if page == HISTORY_PAGE else DUE_PAGE
    return tuple(e for e in ELEMENTS if e[1] == home)


def flip_href(page, current, key: str) -> str:
    """Link that flips one key and stays on `page`."""
    home = page if page == HISTORY_PAGE else DUE_PAGE
    new = toggle(current, key)
    if not new:
        return home
    return f"{home}?optout={new}"


def _split_fragment(href: str) -> tuple:
    """Split off a #fragment (fragment may be empty)."""
    head, sep, tail = href.partition("#")
    return head, (sep + tail)


def carry(href, optout) -> str:
    """Return href with ``?optout=`` appended, or unchanged.

    Unchanged when: no keys opted out, href is not a string, href is
    empty, external (http/https/protocol-relative), a non-navigating
    scheme (mailto:/data:/...), a pure #fragment, or the query already
    carries an optout= parameter (never doubled). Anchors and other
    query params are preserved in place.
    """
    canon = normalize(optout)
    if not canon:
        return href
    if not isinstance(href, str) or not href:
        return href
    low = href.lower()
    if href.startswith(_SKIP_PREFIXES) or low.startswith(_SKIP_PREFIXES):
        return href
    head, frag = _split_fragment(href)
    base, sep, qs = head.partition("?")
    if sep:
        params = qs.split("&")
        if any(p == "optout" or p.startswith("optout=") for p in params):
            return href
        return f"{base}?{qs}&optout={canon}{frag}"
    return f"{base}?optout={canon}{frag}"


def carry_html(html_text, optout) -> str:
    """Rewrite every internal href in a rendered page via carry()."""
    if not normalize(optout):
        return html_text
    if not isinstance(html_text, str) or "href=" not in html_text:
        return html_text
    canon = normalize(optout)

    def _one(m) -> str:
        q, href = m.group(1), m.group(2)
        return f"href={q}{carry(href, canon)}{q}"

    return _HREF_RE.sub(_one, html_text)


def toggle_box_html(current=None, page=DUE_PAGE) -> str:
    """Settings box for one page: per-element hide/show links.

    Lists this page's elements with [x]/[ ] marks and flip links that
    stay on the page; the other page's box is one link away. The
    ``_send`` pass carries the choice onto every link, including these.
    """
    off = parse(current)
    mine = elements_for(page)
    home = HISTORY_PAGE if page == HISTORY_PAGE else DUE_PAGE
    other = DUE_PAGE if home == HISTORY_PAGE else HISTORY_PAGE
    other_name = "Due" if other == DUE_PAGE else "History"
    other_n = len(ELEMENTS) - len(mine)
    showing = sum(1 for k, _p, _l, _m in mine if k not in off)
    rows = []
    for key, _p, label, _m in mine:
        if key in off:
            rows.append(
                f"<li>[ ] {html.escape(label)} (hidden) "
                f"<a href='{flip_href(home, off, key)}'>show</a></li>")
        else:
            rows.append(
                f"<li>[x] {html.escape(label)} "
                f"<a href='{flip_href(home, off, key)}'>hide</a></li>")
    return (
        f"<details id='{BOX_ANCHOR}'>"
        f"<summary>Motivational elements: {showing} of {len(mine)} "
        f"showing on this page</summary><ul>{''.join(rows)}</ul>"
        f"<p><small>{other_n} more live on "
        f"<a href='{other}#{BOX_ANCHOR}'>{other_name}</a>; "
        "choices ride the URL as ?optout= and survive navigation."
        "</small></p></details>")


def section_html() -> str:
    """Anchored status subsection; joined by groundwork/batch26.py."""
    return (
        f"<h3 id='{STATUS_ANCHOR}'>Granular motivational opt-outs "
        "<small>(feature)</small></h3>"
        "<p>Each of the 19 motivational sections - garden, rings, "
        "milestones, bests, badges, mascot, celebrations, and the rest "
        "- hides on its own via <code>?optout=garden,bests</code>. "
        "Choices ride the URL with link carry-over, so no cookies and "
        "no database change; without the parameter every page renders "
        "exactly as before. <code>groundwork/optout.py</code> parses, "
        "gates, and carries; the Due and History pages host the "
        "toggle boxes.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "motivation-toggles",
        "kind": "feature",
        "title": "Granular motivational opt-outs",
        "blurb": "Hide any celebration, garden, mascot, or badge wall on its own - choices ride the URL.",
        "path": DUE_PAGE,
        "anchor": BOX_ANCHOR,
    }
