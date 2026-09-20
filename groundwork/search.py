"""Global header search over concepts, modules, and symbols (I-2).

Pure in-memory ranking over record dicts — no DB I/O here. The web
Handler supplies rows (modules + concepts) and this module ranks,
renders the header box, the `/` focus script, and the results list.

Record shape: {"kind": "concept" | "module" | "symbol",
"title": str, "url": str, "detail": str}.
"""
from __future__ import annotations

import html

LIMIT = 10
INPUT_ID = "site-search"
FORM_ACTION = "/search"


def normalize(query) -> str:
    """Lowercase, collapse whitespace; non-strings become ''."""
    if not isinstance(query, str):
        return ""
    return " ".join(query.lower().split())


def score_record(rec: dict, tokens: list[str]) -> int | None:
    """Rank 0+ for a match, None when any token is absent.

    Title hits weigh 3, detail hits weigh 1; prefix hits double.
    """
    title = str(rec.get("title", "")).lower()
    detail = str(rec.get("detail", "")).lower()
    total = 0
    for tok in tokens:
        hit = 0
        if tok in title:
            hit += 3
            if title.startswith(tok):
                hit += 3
        if tok in detail:
            hit += 1
        if hit == 0:
            return None
        total += hit
    return total


def search(records, query: str, limit: int = LIMIT) -> list[dict]:
    """Best-first matching records; [] on blank query or no match."""
    q = normalize(query)
    if not q:
        return []
    tokens = q.split()
    scored = []
    for rec in records or []:
        score = score_record(rec, tokens)
        if score is not None:
            scored.append((score, str(rec.get("title", "")).lower(), rec))
    scored.sort(key=lambda t: (-t[0], t[1]))
    return [r for _, _, r in scored[:max(0, limit)]]


def modules_to_records(rows) -> list[dict]:
    """Module rows -> search records (url /modules/<id>)."""
    out = []
    for r in rows or []:
        mid = r.get("id", "") if isinstance(r, dict) else r[0]
        summary = r.get("task_summary", "") if isinstance(r, dict) else r[1]
        out.append({"kind": "module", "title": str(mid),
                    "url": f"/modules/{mid}",
                    "detail": str(summary or "")})
    return out


def concepts_to_records(rows) -> list[dict]:
    """Concept rows -> concept records plus symbol records for code kinds.

    Concepts with kind function/class/method also surface as "symbol"
    records pointing at the same lesson anchor, so symbol lookup
    (e.g. a function name) lands on the lesson.
    """
    out = []
    for r in rows or []:
        if isinstance(r, dict):
            cid, mid, name, kind = (r.get("id", ""), r.get("module_id", ""),
                                    r.get("name", ""), r.get("kind", ""))
        else:
            cid, mid, name, kind = r[0], r[1], r[2], r[3]
        url = f"/modules/{mid}"
        out.append({"kind": "concept", "title": str(name),
                    "url": url, "detail": f"{kind} · {cid}"})
        if str(kind) in ("function", "class", "method"):
            out.append({"kind": "symbol", "title": str(name),
                        "url": url, "detail": f"symbol {kind} · {cid}"})
    return out


def header_html(query: str = "") -> str:
    """Header search box; lives in the page header on every page."""
    q = html.escape(query or "", quote=True)
    return (
        f"<form role='search' action='{FORM_ACTION}' method='get'>"
        f"<label for='{INPUT_ID}'>Search</label>"
        f"<input id='{INPUT_ID}' name='q' type='search' value='{q}' "
        f"placeholder='Search concepts, modules, symbols' autocomplete='off'>"
        "<button type='submit'>Go</button>"
        "<small>Press <kbd>/</kbd> to focus</small></form>")


def script_js() -> str:
    """`/` focuses the header box; never fires while typing.

    Compatible with shortcuts.py: `?` still toggles the cheat sheet
    and g-sequences still navigate — `/` only focuses search.
    """
    return f"""
<script>
(function () {{
  document.addEventListener('keydown', function (e) {{
    if (e.key !== '/' || e.ctrlKey || e.metaKey || e.altKey) return;
    var tag = (e.target.tagName || '').toLowerCase();
    if (tag === 'input' || tag === 'textarea' || tag === 'select' ||
        e.target.isContentEditable) return;
    var box = document.getElementById('{INPUT_ID}');
    if (box) {{ e.preventDefault(); box.focus(); }}
  }});
}})();
</script>"""


def results_html(results, query: str) -> str:
    """Ranked hits as a list; empty state offers a next step."""
    q = html.escape(query or "")
    if not results:
        return (f"<p id='search-empty'>No matches for <b>{q}</b>. "
                "Try a concept name, module id, or symbol — or "
                "<a href='/modules'>browse the library</a>.</p>")
    items = "".join(
        f"<li><span class='chip'>{html.escape(str(r.get('kind', '')))}</span> "
        f"<a href='{html.escape(str(r.get('url', '/')), quote=True)}'>"
        f"{html.escape(str(r.get('title', '')))}</a> "
        f"<small>{html.escape(str(r.get('detail', '')))}</small></li>"
        for r in results)
    return (f"<p>{len(results)} match(es) for <b>{q}</b>.</p>"
            f"<ul id='search-results'>{items}</ul>")


def section_html() -> str:
    """Status home for header search (anchor id status-b6-search)."""
    return (
        "<h3 id='status-b6-search'>Header search <small>(improvement)</small></h3>"
        f"<p>One box in the header searches concepts, modules, and symbols; "
        f"press <kbd>/</kbd> to focus from any page. "
        f"<code>groundwork/search.py</code> · form posts to "
        f"<code>{FORM_ACTION}?q=…</code>.</p>")
