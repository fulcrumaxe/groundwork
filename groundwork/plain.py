"""Plain mode: zero-gamification lists over the same engine (F-140).

With ?plain=1 set, finished pages keep their queues, lessons, forms,
calibration and history lists, but every decoration goes: badges,
celebrations, gardens, bests, quests, challenges, wagers, unlock
effects, companion lines and identity art. Grading and scheduling
never see the flag - the strip runs after render in Handler._send,
so the engine is identical by construction.

The flag rides the URL with link carry-over (precedent: levelcarry),
per-browser and bookmarkable, no cookies, no DB/schema changes.
"""
from __future__ import annotations

import html
import re
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit

PARAM = "plain"
ON = "1"
OFF = ""
STATUS_ANCHOR = "status-b26-plain"
NOTICE_ANCHOR = "plain-mode"
TOGGLE_ANCHOR = "plain-toggle"
MAIN_OPEN = "<main id='main'>"

#: Human labels for every stripped decoration (Due, module, History).
STRIPPED = ("mascot", "partytrick", "serendipity", "done-hero",
            "cbadge", "unlock-fx", "quests", "classquests",
            "library-identity", "growth-rings", "knowledge-garden",
            "milestones", "endorsements", "teaching-certificates",
            "showcase", "theme-unlocks", "teamchallenge",
            "seasonal-event", "anniversary", "bests", "status-wagers")

_HREF_RE = re.compile(r"""href=(['"])(.*?)\1""")

_SKIP_PREFIXES = ("#", "http://", "https://", "//", "mailto:",
                  "data:", "javascript:", "tel:")


def normalize(value) -> str:
    """Canonical plain flag: "1" when on, else "" (off keeps links clean)."""
    try:
        text = value.strip() if isinstance(value, str) else ""
    except Exception:  # noqa: BLE001 -- flag parsing never raises
        return OFF
    return ON if text == ON else OFF


def is_plain(value) -> bool:
    """True only for an explicit ?plain=1; everything else is off."""
    return normalize(value) == ON


def _split_fragment(href: str) -> tuple[str, str]:
    """Split off a #fragment (fragment may be empty)."""
    head, sep, tail = href.partition("#")
    return head, (sep + tail)


def carry(href, plain: str) -> str:
    """Return href with ?plain=1 appended, or unchanged.

    Unchanged when: plain mode is off, href is not a string, href
    is empty, external (http/https/protocol-relative), a
    non-navigating scheme (mailto:/data:/...), a pure #fragment, or
    the query already carries a plain= parameter (never doubled).
    Anchors and other query params are preserved in place.
    """
    if not is_plain(plain):
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
        if any(p == PARAM or p.startswith(PARAM + "=") for p in params):
            return href
        return f"{base}?{qs}&{PARAM}={ON}{frag}"
    return f"{base}?{PARAM}={ON}{frag}"


def carry_html(html_text, plain: str) -> str:
    """Rewrite every internal href in a rendered page via carry()."""
    if not is_plain(plain):
        return html_text
    if not isinstance(html_text, str) or "href=" not in html_text:
        return html_text

    def _one(m: "re.Match") -> str:
        q, href = m.group(1), m.group(2)
        return f"href={q}{carry(href, ON)}{q}"

    return _HREF_RE.sub(_one, html_text)


def exit_href(path) -> str:
    """Request path with the plain flag removed (the way back out)."""
    try:
        raw = path if isinstance(path, str) and path else "/"
        bits = urlsplit(raw)
        kept = [(k, v) for k, v in
                parse_qsl(bits.query, keep_blank_values=True) if k != PARAM]
        return urlunsplit(("", "", bits.path or "/", urlencode(kept),
                           bits.fragment))
    except Exception:  # noqa: BLE001 -- exit link never raises
        return "/"


def notice_html(exit="/") -> str:
    """One-line mode banner with the exit link; always safe to render."""
    try:
        href = html.escape(str(exit or "/"), quote=True)
    except Exception:  # noqa: BLE001 -- notice never raises
        href = "/"
    return (f"<p id='{NOTICE_ANCHOR}'>Plain mode - lists only, same grades "
            f"and schedule. <a href='{href}'>Show decorations</a></p>")


def gate(block, plain: str):
    """A decoration block, kept normally and dropped in plain mode."""
    return "" if is_plain(plain) else block


def toggle_link_html(entry: str = "/due") -> str:
    """Entry link into plain mode (the tour target); never raises."""
    try:
        dest = entry if isinstance(entry, str) and entry else "/due"
        href = html.escape(carry(dest, ON), quote=True)
        return (f"<p id='{TOGGLE_ANCHOR}'><small>Prefer lists only? "
                f"<a href='{href}'>Plain mode</a></small></p>")
    except Exception:  # noqa: BLE001 -- entry link never raises
        return ""


def _pattern_list() -> list:
    """(label, regex) pairs, each matching one decoration block exactly.

    Every pattern is self-bounded (its own close tag or exact body
    shape from the source module), so stripping never eats a kept
    neighbor no matter which sections a page joins or omits.
    Gallery patterns precede their h2+p fallbacks.
    """
    pats = []
    for sid in ("partytrick", "serendipity", "done-hero", "quests",
                "classquests", "anniversary"):
        pats.append((f"section#{sid}",
                     rf"<section\b[^>]*\bid='{sid}'[^>]*>.*?</section>"))
    for pid in ("mascot", "library-identity"):
        pats.append((f"p#{pid}",
                     rf"<p\b[^>]*\bid='{pid}'[^>]*>.*?</p>"))
    for cls in ("cbadge", "unlock-fx"):
        pats.append((f"span.{cls}",
                     rf"<span\b[^>]*\bclass='[^']*\b{cls}\b[^']*'[^>]*>"
                     r".*?</span>"))
    pats.append(("wagers",
                 r"<h3\b[^>]*\bid='status-wagers'[^>]*>.*?</form>"))
    pats.append(("theme-gallery",
                 r"<h2\b[^>]*\bid='theme-unlocks'[^>]*>.*?</h2>\s*"
                 r"<div\b[^>]*\bclass='theme-gallery'[^>]*>.*?</script>"))
    pats.append(("theme-fallback",
                 r"<h2\b[^>]*\bid='theme-unlocks'[^>]*>.*?</h2>\s*"
                 r"<p>.*?</p>"))
    for hid in ("bests", "seasonal-event"):
        pats.append((f"h2#{hid}",
                     rf"<h2\b[^>]*\bid='{hid}'[^>]*>.*?</h2>\s*<p>.*?</p>"))
    for hid in ("milestones", "endorsements"):
        pats.append((f"h2#{hid}",
                     rf"<h2\b[^>]*\bid='{hid}'[^>]*>.*?</h2>\s*"
                     r"(?:<ul>.*?</ul>|<p>.*?</p>)"))
    pats.append(("teamchallenge",
                 r"<h2\b[^>]*\bid='teamchallenge'[^>]*>.*?</h2>\s*"
                 r"<p>.*?</p>\s*<ul>.*?</ul>"))
    pats.append(("teaching-certificates",
                 r"<h2\b[^>]*\bid='teaching-certificates'[^>]*>.*?</h2>"
                 r"(?:\s*<p>.*?</p>)+"))
    pats.append(("showcase-gallery",
                 r"<h2\b[^>]*\bid='showcase'[^>]*>.*?</h2>\s*"
                 r"(?:<div\b[^>]*>.*?</div>\s*)+"))
    pats.append(("showcase-fallback",
                 r"<h2\b[^>]*\bid='showcase'[^>]*>.*?</h2>\s*<p>.*?</p>"))
    pats.append(("growth-rings",
                 r"<h2\b[^>]*\bid='growth-rings-head'[^>]*>.*?</h2>\s*"
                 r"(?:<div\b[^>]*\bid='growth-rings'[^>]*>.*?</div>"
                 r"|<p>.*?</p>)"))
    pats.append(("knowledge-garden",
                 r"<h2\b[^>]*\bid='knowledge-garden'[^>]*>.*?</h2>\s*"
                 r"(?:<h3>.*?</h3>\s*<p\b[^>]*\bclass='bed'[^>]*>.*?</p>"
                 r"\s*)+(?:<p><small>\+.*?beyond the fence\.</small></p>)?"))
    pats.append(("knowledge-garden-fallback",
                 r"<h2\b[^>]*\bid='knowledge-garden'[^>]*>.*?</h2>\s*"
                 r"<p>.*?</p>"))
    return pats


_PATTERNS = tuple((label, re.compile(pat, re.DOTALL))
                  for label, pat in _pattern_list())

_NEEDLES = (("mascot", "id='mascot'"),
            ("partytrick", "id='partytrick'"),
            ("serendipity", "id='serendipity'"),
            ("done-hero", "id='done-hero'"),
            ("cbadge", "class='cbadge"),
            ("unlock-fx", "class='unlock-fx"),
            ("quests", "id='quests'"),
            ("classquests", "id='classquests'"),
            ("library-identity", "id='library-identity'"),
            ("growth-rings", "id='growth-rings'"),
            ("growth-rings-head", "id='growth-rings-head'"),
            ("knowledge-garden", "id='knowledge-garden'"),
            ("milestones", "id='milestones'"),
            ("endorsements", "id='endorsements'"),
            ("teaching-certificates", "id='teaching-certificates'"),
            ("showcase", "id='showcase'"),
            ("theme-unlocks", "id='theme-unlocks'"),
            ("teamchallenge", "id='teamchallenge'"),
            ("seasonal-event", "id='seasonal-event'"),
            ("anniversary", "id='anniversary'"),
            ("bests", "id='bests'"),
            ("status-wagers", "id='status-wagers'"))


def stripped_ids(html_text) -> list:
    """Labels of decorations present in the markup; [] when none/hostile."""
    try:
        if not isinstance(html_text, str):
            return []
        return sorted(label for label, needle in _NEEDLES
                      if needle in html_text)
    except Exception:  # noqa: BLE001 -- scanning never raises
        return []


def strip_html(html_text, plain: str, exit="/") -> str:
    """Remove gamification blocks when plain mode is on; else unchanged.

    Off (or non-string input) returns the input object untouched, so
    the legacy path keeps byte-identical output. On, every pattern
    above is removed and the mode notice is injected right after
    <main id='main'> when that shell marker exists.
    """
    if not is_plain(plain):
        return html_text
    if not isinstance(html_text, str):
        return html_text
    try:
        out = html_text
        for _label, rx in _PATTERNS:
            out = rx.sub("", out)
    except Exception:  # noqa: BLE001 -- fail closed, keep decorations
        return html_text
    try:
        note = notice_html(exit)
        if MAIN_OPEN in out:
            out = out.replace(MAIN_OPEN, MAIN_OPEN + note, 1)
    except Exception:  # noqa: BLE001 -- notice must never break the page
        pass
    return out


def section_html() -> str:
    """Anchored status subsection with a live strip demo."""
    try:
        sample = ("<p id='mascot' class='mascot'>Momo is resting.</p>"
                  "<p id='queue'>3 cards due</p>")
        before = len(stripped_ids(sample))
        after = html.escape(strip_html(sample, ON))
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Plain mode <small>(feature)</small></h3>"
            "<p>Zero gamification over the same engine - "
            "<code>groundwork/plain.py</code> strips badges, celebrations, "
            "gardens, bests, quests and companion lines from finished pages "
            f"when <code>?plain=1</code> is set ({before} block removed "
            f"below, the queue kept): <code>{after}</code> "
            "Try <a href='/due?plain=1'>Due in plain mode</a>; grades and "
            "scheduling never see the flag.</p>")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Plain mode</h3>"
                "<p>Plain-mode help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "plain-mode",
        "kind": "feature",
        "title": "Plain mode",
        "blurb": ("Zero gamification with one flag - ?plain=1 strips badges, "
                  "celebrations, gardens and quests while grades and "
                  "schedule stay identical."),
        "path": "/due",
        "anchor": TOGGLE_ANCHOR,
    }
