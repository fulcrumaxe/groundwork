"""Image attachments in concept notes (I-130): screenshots and
whiteboard photos rendered in lessons.

Agents filing a module increasingly note "see screenshot" or paste a
whiteboard photo reference in ``concept_notes``; without rendering that
image stays invisible and the lesson text loses its visual anchor.
``attachments_in`` collects image evidence for one lesson from an
``attachments`` list on the lesson frame plus ``![alt](src)`` refs
scanned out of the lesson's concept notes, and ``figures_html``
renders them as escaped ``<figure>`` blocks on the lesson rendering
path. Lessons without images render "" (byte-identical legacy path).
Stdlib only (``html``, ``re``); no I/O, never raises.

Caller path (real learner/reader, never a Status demo):
``Handler.module_html`` appends ``figures_html(lesson_map[node])``
once per lesson section. The raw concept-notes mapping exists only
at module-creation time; at render time notes survive as the
lesson's ``why_note`` string (I-109), so ``attachments_in`` also
scans ``why_note`` for ``![alt](src)`` refs beside the ``attachments``
list and an optional notes mapping.
"""
from __future__ import annotations

import html
import re

STATUS_ANCHOR = "status-b21-imgattach"

MAX_ATTACHMENTS = 6
MAX_SRC = 500
MAX_ALT = 200
ALLOWED_EXTS = (".png", ".jpg", ".jpeg", ".gif", ".webp")

_IMAGE_RE = re.compile(r"!\[([^\]]{0,200})\]\(([^)\s]{1,500})\)")


def _safe_src(src) -> str:
    """Usable image src: relative/attached path, http(s) URL, or
    data:image payload; anything else -> ""."""
    try:
        if not isinstance(src, str):
            return ""
        text = src.strip()
        if not text or len(text) > MAX_SRC:
            return ""
        low = text.lower()
        if low.startswith("data:image/"):
            kind = low[len("data:image:"):].split(";", 1)[0]
            if kind in ("png", "jpeg", "gif", "webp"):
                return text
            return ""
        if low.startswith(("http://", "https://")):
            path = low.split("?", 1)[0].rsplit("#", 1)[0]
            if path.endswith(ALLOWED_EXTS):
                return text
            return ""
        if re.match(r"^[a-zA-Z][a-zA-Z0-9+.-]*:", text):
            return ""
        if text.startswith(("/", "\\")) or ".." in text.split("/"):
            return ""
        path = low.split("?", 1)[0].rsplit("#", 1)[0]
        if path.endswith(ALLOWED_EXTS):
            return text
        return ""
    except Exception:  # noqa: BLE001 -- cleaning never raises
        return ""


def clean_attachment(entry) -> dict | None:
    """Normalized {src, alt, caption} for one attachment; None when unusable."""
    try:
        alt, caption = "", ""
        if isinstance(entry, str):
            src = _safe_src(entry)
        elif isinstance(entry, dict):
            src = _safe_src(entry.get("src"))
            raw_alt = entry.get("alt", "")
            if isinstance(raw_alt, str):
                alt = raw_alt.strip()[:MAX_ALT]
            raw_cap = entry.get("caption", "")
            if isinstance(raw_cap, str):
                caption = raw_cap.strip()[:MAX_ALT]
        else:
            return None
        if not src:
            return None
        if not alt:
            alt = src.rsplit("/", 1)[-1].rsplit("?", 1)[0][:MAX_ALT]
        return {"src": src, "alt": alt, "caption": caption}
    except Exception:  # noqa: BLE001 -- cleaning never raises
        return None


def images_in_text(text) -> list:
    """Markdown ``![alt](src)`` refs in one note; hostile input -> []."""
    try:
        if not isinstance(text, str) or not text:
            return []
        out = []
        for match in _IMAGE_RE.finditer(text):
            got = clean_attachment({"src": match.group(2),
                                    "alt": match.group(1)})
            if got is not None:
                out.append(got)
        return out
    except Exception:  # noqa: BLE001 -- scanning never raises
        return []


def attachments_in(lesson, notes=None) -> list:
    """Image attachments for one lesson, capped at MAX_ATTACHMENTS.

    Keys tried in order: ``attachments`` list on the lesson frame,
    then ``![alt](src)`` refs scanned from a notes mapping (concept_id,
    then name -- mirrors the pipeline note lookup), then ``![alt](src)``
    refs in the lesson's own ``why_note`` (the render-time carrier of
    concept notes; the raw mapping exists only at creation time).
    Anything hostile contributes nothing. Never raises.
    """
    try:
        found: list = []
        if isinstance(lesson, dict):
            raw = lesson.get("attachments")
            if isinstance(raw, list):
                for entry in raw:
                    got = clean_attachment(entry)
                    if got is not None:
                        found.append(got)
            if isinstance(notes, dict):
                for key in (lesson.get("concept_id"), lesson.get("name")):
                    if key is not None and key in notes:
                        found.extend(images_in_text(notes[key]))
            why = lesson.get("why_note")
            if isinstance(why, str) and why:
                found.extend(images_in_text(why))
        return found[:MAX_ATTACHMENTS]
    except Exception:  # noqa: BLE001 -- lookup never raises
        return []


def figures_html(lesson, notes=None) -> str:
    """``<div class='concept-shots'>`` figures; "" when no images.

    Sources and alt text are escaped; images load lazily so a
    photo-heavy lesson never blocks first paint. Never raises.
    """
    try:
        shots = attachments_in(lesson, notes)
        if not shots:
            return ""
        esc = html.escape
        figs = []
        for shot in shots:
            cap = (f"<figcaption>{esc(shot['caption'])}</figcaption>"
                   if shot["caption"] else "")
            figs.append(
                f"<figure class='concept-shot'>"
                f"<img src='{esc(shot['src'], quote=True)}'"
                f" alt='{esc(shot['alt'], quote=True)}'"
                f" loading='lazy'>{cap}</figure>")
        return f"<div class='concept-shots'>{''.join(figs)}</div>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def section_html() -> str:
    """Anchored status subsection; joined by the batch21 home module."""
    try:
        sample = figures_html({"attachments": [
            {"src": "shots/whiteboard1.png", "alt": "Whiteboard sketch"}]})
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Concept-note images in lessons "
            "<small>(improvement)</small></h3>"
            "<p>Screenshots and whiteboard photos attached to a concept "
            "note render inline in the lesson -- escaped, lazy-loaded, "
            "capped at six per lesson; lessons without images render "
            "exactly as before. "
            "<code>groundwork/imgattach.py</code> provides "
            "<code>attachments_in()</code>/<code>figures_html()</code>; "
            "the module page calls it once per lesson section. A live "
            "sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must never raise
        return (f"<h3 id='{STATUS_ANCHOR}'>Concept-note images in "
                "lessons</h3>"
                "<p>Lesson-image help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "concept-images",
        "kind": "improvement",
        "title": "Screenshots and whiteboard photos in lessons",
        "blurb": ("Images attached to a concept note render inline in "
                  "its lesson -- screenshots and whiteboard shots included."),
        "path": "/status",
        "anchor": STATUS_ANCHOR,
    }
