"""Module storage: plain Markdown + YAML front matter (PRD principle 5).

Modules can be diffed, shared and hand-edited. Stored in SQLite (source_markdown)
and mirrored to <repo>/.groundwork/modules/<id>.md when a repo path is given.
"""
from __future__ import annotations

import json
import uuid
from pathlib import Path


def _yaml_block(meta: dict) -> str:
    lines = ["---"]
    for k, v in meta.items():
        if isinstance(v, list):
            lines.append(f"{k}: [{', '.join(str(i) for i in v)}]")
        else:
            lines.append(f"{k}: {v}")
    lines.append("---")
    return "\n".join(lines) + "\n"


def to_markdown(module_id: str, meta: dict, exercises: list[dict],
                lessons: list[dict] | None = None) -> str:
    parts = [_yaml_block({"id": module_id, **meta})]
    parts.append(f"# Module {module_id}\n")
    if lessons:
        from . import explain as explainmod
        parts.append("## Study guide (read this first)\n")
        for L in lessons:
            parts.append(f"### `{L['name']}` — {L['kind']} "
                         f"(`{L['file']}:{L['line']}`)\n")
            parts.append(L["summary"] + "\n")
            if L.get("docstring"):
                parts.append(f"> {L['docstring'].splitlines()[0]}\n")
            if L.get("how"):
                parts.append("How it works, step by step:\n")
                parts += [f"{i + 1}. {s}" for i, s in enumerate(L["how"])]
                parts.append("")
            w = L.get("worked")
            if w:
                if w.get("call") and w.get("output") is not None:
                    parts.append(f"Watch it run: `{w['call']}` → `{w['output']}`\n")
                if w.get("trace"):
                    t = w["trace"]
                    parts.append(f"Trace of `{t['var']}`: "
                                 + " → ".join(f"`{v}`" for v in t["steps"][:8]) + "\n")
            source = L.get("source") or L.get("key_lines", "")
            if source:
                parts.append(f"```\n{source[:2000]}\n```\n")
            for lv in explainmod.levels_for(L):
                parts.append(f"### {lv['title']}\n")
                for blk in lv["blocks"]:
                    if blk.get("pre"):
                        continue  # full source already shown above
                    parts.append(f"**{blk['h']}:** {blk['b']}\n")
            rel = []
            if L.get("callers"):
                rel.append("used by " + ", ".join(f"`{c}`" for c in L["callers"][:4]))
            if L.get("callees"):
                rel.append("works with " + ", ".join(f"`{c}`" for c in L["callees"][:4]))
            if rel:
                parts.append("Fits in: " + "; ".join(rel) + ".\n")
    for ex in exercises:
        parts.append(f"## {ex.get('concept', '')} · {ex.get('type_name', ex.get('type'))}\n")
        parts.append(f"- id: `{ex.get('id')}`")
        parts.append(f"- bloom: {ex.get('bloom')}")
        parts.append(f"- anchor: `{ex.get('file', '')}:{ex.get('line', 0)} @ {ex.get('commit', '')}`\n")
        parts.append(ex.get("front", ""))
        parts.append(f"\n<details><summary>Answer</summary>\n\n{ex.get('back', '')}\n\n</details>\n")
        parts.append(f"```json\n{json.dumps(ex.get('payload', {}))}\n```\n")
    return "\n".join(parts)


def new_id() -> str:
    return uuid.uuid4().hex[:12]


def save_module(con, module_id: str, repo: str, commit_range: str,
                summary: str, level: str, exercises: list[dict],
                concepts: list, lessons: list[dict] | None = None,
                purpose: str = "") -> str:
    meta = {"repo": repo, "commit_range": commit_range, "summary": summary,
            "learner_level": level, "purpose": purpose,
            "concepts": [c.node_id for c in concepts]}
    md = to_markdown(module_id, meta, exercises, lessons)
    con.execute(
        "INSERT INTO modules(id, repo, commit_range, task_summary, learner_level, source_markdown, lessons, purpose)"
        " VALUES(?,?,?,?,?,?,?,?)",
        (module_id, repo, commit_range, summary, level, md,
         json.dumps(lessons or []), purpose))
    for c in concepts:
        cid = f"{module_id}:{c.node_id}"
        try:
            fhash = _file_hash(repo, c.file)
        except OSError:
            fhash = ""
        con.execute(
            "INSERT INTO concepts(id, module_id, name, kind, file, line, file_hash, bloom)"
            " VALUES(?,?,?,?,?,?,?,?)",
            (cid, module_id, c.name, c.kind, c.file, c.line, fhash, "recall"))
    for ex in exercises:
        # Namespace card ids per module: every module numbers its own
        # exercises ex001…, so bare ids collide on the second module
        # ever saved to the same database.
        card_id = f"{module_id}:{ex['id']}"
        payload = dict(ex.get("payload", {}))
        payload["hints"] = ex.get("hints", [])
        if ex.get("why"):
            payload["why"] = ex["why"]
        con.execute(
            "INSERT INTO cards(id, concept_id, exercise_type, front, back, payload)"
            " VALUES(?,?,?,?,?,?)",
            (card_id, f"{module_id}:{ex['concept_id']}", str(ex["type"]),
             ex.get("front", ""), ex.get("back", ""),
             json.dumps(payload)))
    con.commit()
    # Mirror to repo dir for hand-editing/sharing.
    try:
        mdir = Path(repo) / ".groundwork" / "modules"
        mdir.mkdir(parents=True, exist_ok=True)
        (mdir / f"{module_id}.md").write_text(md, encoding="utf-8")
    except OSError:
        pass
    return module_id


def _file_hash(repo: str, file: str) -> str:
    import hashlib
    h = hashlib.sha256()
    with open(Path(repo) / file, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]


def mark_stale_cards(con, repo: str) -> int:
    """Compare stored file hashes; flag changed cards stale. Returns count."""
    n = 0
    for row in con.execute(
            "SELECT cards.id, concepts.file, concepts.file_hash FROM cards"
            " JOIN concepts ON concepts.id = cards.concept_id"):
        try:
            cur = _file_hash(repo, row["file"])
        except OSError:
            continue
        if cur != row["file_hash"]:
            con.execute("UPDATE cards SET stale=1 WHERE id=?", (row["id"],))
            n += 1
    con.commit()
    return n
