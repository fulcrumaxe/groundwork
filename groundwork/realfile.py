"""See-it-in-the-real-file links plus a read-only repo viewer (I-129).

Lesson headers already name the concept's file and line; now they
link there. The ``/file`` viewer serves repo text files with every
line anchored (``#L<n>``) and the concept's line highlighted, so a
"see it in the real file" click lands on the exact line. The viewer
is read-only and jailed: the path must resolve inside the repo root
(the served DB's directory), stay under a size cap, and decode as
UTF-8 text — traversal, absolute, binary, and oversize requests get
a refusal page, never a traceback. Pure functions plus one thin
route; no schema change.

Caller paths (lesson rendering + routing, never a Status demo):
``Handler.module_html`` appends ``file_link`` to each concept
header (first link carries the tour anchor); ``do_GET`` delegates
``/file`` to ``page_html``. Without a usable file/line the header
renders byte-identical. Never raises.
"""
from __future__ import annotations

import html
import os
from urllib.parse import quote

STATUS_ANCHOR = "status-b22-realfile"

#: Refuse anything bigger; the viewer shows code, not dumps.
MAX_BYTES = 256 * 1024


def file_link(file, line, first: bool = False) -> str:
    """"See it in the real file" link for a concept header.

    "" when the file/line is unusable so headers without source
    render byte-identical. The first link on the page carries the
    tour anchor. Never raises.
    """
    try:
        name = str(file or "").strip()
        n = int(line or 0)
        if not name or "\x00" in name or n < 1:
            return ""
        href = (f"/file?path={quote(name, safe='')}&line={n}#L{n}")
        mark = " id='realfile'" if first else ""
        return f" · <a{mark} href='{href}'>see it in the real file</a>"
    except Exception:  # noqa: BLE001 -- links never raise
        return ""


def db_root(db_path) -> str:
    """Serving repo root: the served DB's directory. Never raises."""
    try:
        return os.path.dirname(os.path.abspath(str(db_path or ""))) or "."
    except Exception:  # noqa: BLE001 -- roots never raise
        return "."


def _resolve(root, path):
    """Absolute path inside root, or None. Never raises."""
    try:
        base = os.path.realpath(str(root or ""))
        name = str(path or "").strip().replace("\\", "/")
        if not name or name.startswith("/") or "\x00" in name:
            return None
        full = os.path.realpath(os.path.join(base, *name.split("/")))
        if full != base and not full.startswith(base + os.sep):
            return None
        return full
    except Exception:  # noqa: BLE001 -- resolution never raises
        return None


def _read_lines(full: str):
    """[(n, text)] for a small UTF-8 text file, else None."""
    try:
        if not os.path.isfile(full):
            return None
        if os.path.getsize(full) > MAX_BYTES:
            return None
        with open(full, "rb") as f:
            raw = f.read(MAX_BYTES + 1)
        if len(raw) > MAX_BYTES or b"\x00" in raw:
            return None
        text = raw.decode("utf-8")
    except Exception:  # noqa: BLE001 -- unreadable is a refusal
        return None
    if not isinstance(text, str):
        return None
    try:
        return list(enumerate(text.split("\n"), 1))
    except Exception:  # noqa: BLE001 -- splitting never raises
        return None


def lines_html(numbered, target: int = 0) -> str:
    """Numbered-line <pre> block; the target line anchors + highlights.

    ``numbered`` is [(n, text)]; hostile input yields "". Never raises.
    """
    try:
        rows = list(numbered or [])
    except TypeError:
        return ""
    try:
        target_i = int(target or 0)
    except (TypeError, ValueError):
        target_i = 0
    try:
        out = []
        for n, text in rows:
            try:
                num, code = int(n), html.escape(str(text))
            except Exception:  # noqa: BLE001 -- one bad row skips
                continue
            at = " class='at'" if num == target_i and target_i else ""
            out.append(f"<span id='L{num}'{at}>{num:4d}  {code}</span>")
        if not out:
            return ""
        return "<pre class='file'>\n" + "\n".join(out) + "\n</pre>"
    except Exception:  # noqa: BLE001 -- markup never raises
        return ""


def page_html(root, path, line) -> tuple:
    """(title, body) for the /file route; refusals explain, never 500."""
    try:
        name = str(path or "").strip()
        full = _resolve(root, name)
        if full is None:
            return ("Not found",
                    "<p>That path stays outside the repo — the viewer "
                    "only serves files under the library root.</p>")
        rows = _read_lines(full)
        if rows is None:
            return ("Not found",
                    f"<p>{html.escape(name)} is not a readable text "
                    "file under the size cap.</p>")
        try:
            want = max(1, min(int(line or 1), len(rows)))
        except (TypeError, ValueError):
            want = 1
        body = (f"<p><small>{html.escape(name)} · line {want} of "
                f"{len(rows)}</small></p>"
                + lines_html(rows, want))
        return (f"File: {name}", body)
    except Exception:  # noqa: BLE001 -- the route never 500s
        return ("Not found", "<p>The viewer hit an unexpected error.</p>")


def status_section_html() -> str:
    """Anchored status subsection; wired into the status page by the parent."""
    try:
        sample = lines_html([(1, "def add(a, b):"), (2, "    return a + b")],
                            2)
        return (
            f"<h3 id='{STATUS_ANCHOR}'>Real-file viewer "
            "<small>(improvement)</small></h3>"
            "<p>Lesson headers link to the exact source line — "
            "<code>groundwork/realfile.py</code> serves repo text files "
            "read-only and jailed to the library root (traversal, "
            "binary, and oversize requests get refusals), every line "
            "anchored. A live sample renders below.</p>"
            f"{sample}")
    except Exception:  # noqa: BLE001 -- status must always render
        return (f"<h3 id='{STATUS_ANCHOR}'>Real-file viewer</h3>"
                "<p>Viewer help temporarily unavailable.</p>")


def tour_entry() -> dict:
    """Tour catalog entry for this item; the parent appends it to ENTRIES."""
    return {
        "id": "real-file",
        "kind": "improvement",
        "title": "See it in the real file",
        "blurb": ("Every concept header links to its exact source line "
                  "in a read-only viewer."),
        "path": "/modules/{mid}",
        "anchor": "realfile",
    }
