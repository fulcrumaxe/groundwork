"""Milestone share-cards: exportable PNGs, opt-in (F-108).

A milestone becomes a small flat PNG (stdlib ``zlib`` + ``struct``;
no Pillow, no network) embedded as a data-URI download link, so the
card is private until the learner chooses to download it. Text
renders in a hand-authored 3x5 bitmap font scaled up — the only way
to draw words with no font files and no dependencies. Pure
functions; card content comes from milestones.moments (existing
tables, no schema change).

Caller path (History page, never a Status demo):
``history.history_html`` appends ``section_html`` in both branches.
The section always renders (anchor-stable for the tour); before the
first milestone it explains the opt-in instead of showing cards.
Never raises.
"""
from __future__ import annotations

import html
import struct
import zlib

from . import milestones as momentsmod

STATUS_ANCHOR = "status-b22-sharecards"

CARD_W = 480
CARD_H = 240
BG = (255, 253, 248)
INK = (26, 26, 26)
ACCENT = (46, 125, 50)

#: 3x5 bitmap font: "#" = ink pixel. Covers card copy (A-Z 0-9 plus
#: a little punctuation); unknown glyphs fall back to "?".
FONT = {
    " ": ("...", "...", "...", "...", "..."),
    "0": ("###", "#.#", "#.#", "#.#", "###"),
    "1": (".#.", "##.", ".#.", ".#.", "###"),
    "2": ("###", "..#", "###", "#..", "###"),
    "3": ("###", "..#", ".##", "..#", "###"),
    "4": ("#.#", "#.#", "###", "..#", "..#"),
    "5": ("###", "#..", "###", "..#", "###"),
    "6": ("###", "#..", "###", "#.#", "###"),
    "7": ("###", "..#", "..#", ".#.", ".#."),
    "8": ("###", "#.#", "###", "#.#", "###"),
    "9": ("###", "#.#", "###", "..#", "###"),
    "A": (".#.", "#.#", "###", "#.#", "#.#"),
    "B": ("##.", "#.#", "##.", "#.#", "##."),
    "C": (".##", "#..", "#..", "#..", ".##"),
    "D": ("##.", "#.#", "#.#", "#.#", "##."),
    "E": ("###", "#..", "##.", "#..", "###"),
    "F": ("###", "#..", "##.", "#..", "#.."),
    "G": (".##", "#..", "#.#", "#.#", ".##"),
    "H": ("#.#", "#.#", "###", "#.#", "#.#"),
    "I": ("###", ".#.", ".#.", ".#.", "###"),
    "J": ("..#", "..#", "..#", "#.#", ".#."),
    "K": ("#.#", "#.#", "##.", "#.#", "#.#"),
    "L": ("#..", "#..", "#..", "#..", "###"),
    "M": ("#.#", "###", "###", "#.#", "#.#"),
    "N": ("#.#", "###", "###", "#.#", "#.#"),
    "O": (".#.", "#.#", "#.#", "#.#", ".#."),
    "P": ("##.", "#.#", "##.", "#..", "#.."),
    "Q": (".#.", "#.#", "#.#", "##.", ".##"),
    "R": ("##.", "#.#", "##.", "#.#", "#.#"),
    "S": (".##", "#..", ".#.", "..#", "##."),
    "T": ("###", ".#.", ".#.", ".#.", ".#."),
    "U": ("#.#", "#.#", "#.#", "#.#", "###"),
    "V": ("#.#", "#.#", "#.#", "#.#", ".#."),
    "W": ("#.#", "#.#", "###", "###", "#.#"),
    "X": ("#.#", "#.#", ".#.", "#.#", "#.#"),
    "Y": ("#.#", "#.#", ".#.", ".#.", ".#."),
    "Z": ("###", "..#", ".#.", "#..", "###"),
    "-": ("...", "...", "###", "...", "..."),
    ".": ("...", "...", "...", "...", ".#."),
    ":": ("...", ".#.", "...", ".#.", "..."),
    "/": ("..#", "..#", ".#.", "#..", "#.."),
    "!": (".#.", ".#.", ".#.", "...", ".#."),
    ",": ("...", "...", "...", ".#.", "#.."),
    "'": (".#.", ".#.", "...", "...", "..."),
    "(": ("..#", ".#.", ".#.", ".#.", "..#"),
    ")": ("#..", ".#.", ".#.", ".#.", "#.."),
    "_": ("...", "...", "...", "...", "###"),
    "?": ("###", "..#", ".#.", "...", ".#."),
}


def _sanitize(text) -> str:
    """Uppercase card copy; anything undrawable becomes ? or space."""
    try:
        out = []
        for ch in str(text or "").upper():
            if ch in FONT:
                out.append(ch)
            elif ch in ("_",):
                out.append("_")
            elif ch.isspace():
                out.append(" ")
            else:
                out.append("?")
        return "".join(out)
    except Exception:  # noqa: BLE001 -- sanitizing never raises
        return ""


def _new(w: int, h: int) -> bytearray:
    buf = bytearray(w * h * 3)
    for i in range(0, len(buf), 3):
        buf[i], buf[i + 1], buf[i + 2] = BG
    return buf


def _px(buf, w: int, h: int, x: int, y: int, color) -> None:
    if 0 <= x < w and 0 <= y < h:
        o = (y * w + x) * 3
        buf[o], buf[o + 1], buf[o + 2] = color


def _text(buf, w: int, h: int, x: int, y: int, text: str,
          scale: int = 4, color=INK) -> int:
    """Draw one line; returns the pixel width drawn. Never raises."""
    try:
        cx = int(x)
        for ch in _sanitize(text):
            glyph = FONT.get(ch, FONT["?"])
            for r, row in enumerate(glyph):
                for c, dot in enumerate(row):
                    if dot == "#":
                        for dy in range(scale):
                            for dx in range(scale):
                                _px(buf, w, h,
                                    cx + c * scale + dx,
                                    int(y) + r * scale + dy, color)
            cx += 4 * int(scale)
        return cx - int(x)
    except Exception:  # noqa: BLE001 -- drawing never raises
        return 0


def _rect(buf, w: int, h: int, color) -> None:
    for x in range(w):
        for y in (0, 1, h - 2, h - 1):
            _px(buf, w, h, x, y, color)
    for y in range(h):
        for x in (0, 1, w - 2, w - 1):
            _px(buf, w, h, x, y, color)


def _chunk(ctype: bytes, data: bytes) -> bytes:
    out = struct.pack(">I", len(data)) + ctype + data
    return out + struct.pack(">I", zlib.crc32(ctype + data) & 0xFFFFFFFF)


def png_bytes(lines) -> bytes:
    """Minimal truecolor PNG for card text lines [(text, scale, color)].

    Hostile input yields a blank card, never an exception.
    """
    try:
        items = [(str(t or ""), max(1, min(8, int(s or 4))),
                  c if isinstance(c, tuple) and len(c) == 3 else INK)
                 for t, s, c in (lines or [])]
    except Exception:  # noqa: BLE001 -- bad lines become a blank card
        items = []
    try:
        buf = _new(CARD_W, CARD_H)
        _rect(buf, CARD_W, CARD_H, ACCENT)
        y = 28
        for text, scale, color in items:
            if y + 5 * scale > CARD_H - 20:
                break
            _text(buf, CARD_W, CARD_H, 32, y, text, scale, color)
            y += 5 * scale + 10
        raw = b"".join(b"\x00" + bytes(buf[r * CARD_W * 3:
                                           (r + 1) * CARD_W * 3])
                       for r in range(CARD_H))
        return (b"\x89PNG\r\n\x1a\n"
                + _chunk(b"IHDR", struct.pack(">IIBBBBB", CARD_W, CARD_H,
                                              8, 2, 0, 0, 0))
                + _chunk(b"IDAT", zlib.compress(raw, 9))
                + _chunk(b"IEND", b""))
    except Exception:  # noqa: BLE001 -- encoding never raises
        return b""


def card_for(kind, label, when) -> bytes:
    """PNG for one milestone; hostile input yields a blank card."""
    try:
        date = str(when or "")[:10]
        return png_bytes([
            ("GROUNDWORK - MILESTONE", 2, ACCENT),
            (str(label or "MILESTONE"), 3, INK),
            (date, 2, INK),
        ])
    except Exception:  # noqa: BLE001 -- cards never raise
        return b""


def card_data_uri(kind, label, when) -> str:
    """Download-ready data URI; "" when encoding fails."""
    try:
        import base64
        raw = card_for(kind, label, when)
        if not raw:
            return ""
        return ("data:image/png;base64,"
                + base64.b64encode(raw).decode("ascii"))
    except Exception:  # noqa: BLE001 -- URIs never raise
        return ""


def section_html(db_path: str) -> str:
    """Always-rendered History section; the anchor never moves."""
    try:
        ms = momentsmod.moments(db_path)
        if not ms:
            body = ("<p>Share cards appear with your first milestone — "
                    "private until you download one. Nothing leaves this "
                    "page unless you say so.</p>")
        else:
            cards = []
            for m in ms:
                uri = card_data_uri(m["kind"], m["label"], m["when"])
                if not uri:
                    continue
                name = _sanitize(m["label"]).strip().lower().replace(
                    " ", "-") or "milestone"
                cards.append(
                    f"<p><b>{html.escape(str(m['label']))}</b> — "
                    f"<small>{html.escape(str(m['when'])[:10])}</small><br>"
                    f"<a class='btn' download='{name}.png' "
                    f"href='{uri}'>Download PNG</a></p>")
            body = "".join(cards) or "<p>Cards temporarily unavailable.</p>"
        return f"<h2 id='share-cards'>Milestone share-cards</h2>{body}"
    except Exception:  # noqa: BLE001 -- history never breaks
        return ("<h2 id='share-cards'>Milestone share-cards</h2>"
                "<p>Cards temporarily unavailable.</p>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        uri = card_data_uri("first-owned", "FIRST OWNED", "2026-01-05")
        img = (f"<p><img src='{uri}' width='240' alt='Sample milestone "
               "share card'></p>" if uri else "")
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Milestone share-cards "
            "<small>(feature)</small></h3>"
            "<p>Opt-in PNG export for milestones — "
            "<code>groundwork/sharecards.py</code> encodes a flat card "
            "with a hand-authored 3x5 bitmap font (stdlib "
            "<code>zlib</code>/<code>struct</code> only, no Pillow) and "
            "the History page offers it as a data-URI download, private "
            "until you click. A live sample renders below.</p>"
            f"{img}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Milestone share-cards</h3>"
                "<p>Cards help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "milestone-share-cards",
        "kind": "feature",
        "title": "Milestone share-cards",
        "blurb": ("Your proof as a PNG — private until you download, "
                  "yours to post."),
        "path": "/reviews",
        "anchor": "share-cards",
    }
