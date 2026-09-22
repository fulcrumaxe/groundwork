"""Git diff reader: unified diff -> hunks with commit + file/line anchors."""
from __future__ import annotations

import re
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

_HUNK = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")
_DIFF_GIT = re.compile(r"^diff --git a/(.*) b/(.*)$")


@dataclass
class Hunk:
    file: str
    start: int
    count: int
    lines: list[str] = field(default_factory=list)


@dataclass
class Diff:
    files: list[str] = field(default_factory=list)
    hunks: list[Hunk] = field(default_factory=list)
    commits: list[str] = field(default_factory=list)


def parse_unified_diff(text: str) -> Diff:
    d = Diff()
    cur_file = ""
    cur_hunk: Hunk | None = None
    lineno = 0
    for raw in text.splitlines():
        m = _DIFF_GIT.match(raw)
        if m:
            cur_file = m.group(2)
            if cur_file not in d.files:
                d.files.append(cur_file)
            cur_hunk = None
            continue
        m = _HUNK.match(raw)
        if m:
            start = int(m.group(1))
            count = int(m.group(2) or "1")
            cur_hunk = Hunk(file=cur_file, start=start, count=count)
            d.hunks.append(cur_hunk)
            lineno = start
            continue
        if cur_hunk is not None and cur_file:
            if raw.startswith(("+", " ", "\\")):
                cur_hunk.lines.append(raw[1:] if raw[0] != "\\" else raw)
                if not raw.startswith("-"):
                    lineno += 1
    return d


def read_diff(repo: str | Path, commit_range: str = "") -> Diff:
    """Read diff for working tree (no range) or a git range like HEAD~1..HEAD."""
    repo = Path(repo)
    if commit_range:
        cmd = ["git", "-C", str(repo), "log", "--format=%H", commit_range]
        try:
            out = subprocess.run(cmd, capture_output=True, text=True,
                                 timeout=30).stdout.strip().split()
            commits = [c for c in out if c]
        except (subprocess.SubprocessError, OSError):
            commits = []
        cmd = ["git", "-C", str(repo), "diff", commit_range]
    else:
        commits = []
        cmd = ["git", "-C", str(repo), "diff"]
    try:
        proc = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        text = proc.stdout
    except (subprocess.SubprocessError, OSError):
        text = ""
    d = parse_unified_diff(text)
    d.commits = commits
    if not d.files and not commit_range:
        # No git diff (not a repo / clean tree): treat changed .py/.ts as full-file.
        for ext in (".py", ".ts", ".tsx", ".js"):
            for p in sorted(repo.rglob(f"*{ext}")):
                if ".git" in p.parts or "node_modules" in p.parts:
                    continue
                rel = str(p.relative_to(repo))
                d.files.append(rel)
                try:
                    lines = p.read_text(encoding="utf-8").splitlines()
                except OSError:
                    lines = []
                d.hunks.append(Hunk(file=rel, start=1, count=len(lines),
                                    lines=lines))
    return d


def head_commit(repo: str | Path) -> str:
    """Current HEAD full hash, or "" outside a git repo; never raises."""
    try:
        proc = subprocess.run(
            ["git", "-C", str(repo), "rev-parse", "HEAD"],
            capture_output=True, text=True, timeout=10)
        text = (proc.stdout or "").strip().lower()
        if len(text) == 40 and all(c in "0123456789abcdef" for c in text):
            return text
        return ""
    except (subprocess.SubprocessError, OSError, ValueError):
        return ""
    except Exception:  # noqa: BLE001 -- lookup never raises
        return ""


def touched_symbols(diff: Diff, graph) -> list[str]:
    """Map diff hunks to graph node ids overlapping the changed lines."""
    by_file: dict[str, list] = {}
    for n in graph.nodes.values():
        by_file.setdefault(n.file, []).append(n)
    hits: list[str] = []
    for h in diff.hunks:
        for n in by_file.get(h.file, []):
            end = h.start + max(h.count, 1)
            # Node overlaps the hunk if its def line is near/inside it.
            if h.start - 5 <= n.line <= end + 5 and n.id not in hits:
                hits.append(n.id)
    return hits
