"""Knowledge-graph ingest: Understand-Anything adapter + built-in Python/TS pass.

Node: {id, name, kind, file, line, imports, calls, hash}
Edge: (src_id, dst_id, kind) where kind in {calls, imports, defines}.
"""
from __future__ import annotations

import ast
import hashlib
import json
import re
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class Node:
    id: str
    name: str
    kind: str  # function | class | module | method
    file: str
    line: int = 0
    calls: list[str] = field(default_factory=list)
    complexity: int = 1  # statement-count proxy


@dataclass
class Graph:
    nodes: dict[str, Node] = field(default_factory=dict)
    edges: list[tuple[str, str, str]] = field(default_factory=list)

    def add(self, node: Node) -> None:
        self.nodes[node.id] = node

    def out_degree(self, nid: str) -> int:
        return sum(1 for s, d, _ in self.edges if s == nid or d == nid)


# ---------------------------------------------------------------- UA adapter

def load_ua_graph(ua_path: str | Path) -> Graph:
    """Load Understand-Anything's .ua/knowledge-graph.json.

    Accepts {nodes:[{id,name,type,file,line}...], edges:[{from,to,type}...]}
    and lenient variants (symbols/links keys, src/dst keys).
    """
    data = json.loads(Path(ua_path).read_text(encoding="utf-8"))
    raw_nodes = data.get("nodes") or data.get("symbols") or []
    raw_edges = data.get("edges") or data.get("links") or []
    g = Graph()
    for n in raw_nodes:
        if not isinstance(n, dict):
            continue
        nid = str(n.get("id") or f"{n.get('file','')}:{n.get('name','')}")
        g.add(Node(
            id=nid,
            name=str(n.get("name", nid)),
            kind=str(n.get("type", n.get("kind", "function"))),
            file=str(n.get("file", "")),
            line=int(n.get("line", 0) or 0),
        ))
    for e in raw_edges:
        if not isinstance(e, dict):
            continue
        s = str(e.get("from", e.get("src", e.get("source", ""))))
        d = str(e.get("to", e.get("dst", e.get("target", ""))))
        if s and d:
            g.edges.append((s, d, str(e.get("type", e.get("kind", "calls")))))
    return g


def find_ua_graph(repo: str | Path) -> Path | None:
    for cand in (Path(repo) / ".ua" / "knowledge-graph.json",
                 Path(repo) / "knowledge-graph.json"):
        if cand.is_file():
            return cand
    return None


# ------------------------------------------------------- built-in Python pass

class _PyVisitor(ast.NodeVisitor):
    def __init__(self, file: str):
        self.file = file
        self.stack: list[str] = []
        self.nodes: list[Node] = []
        self.edges: list[tuple[str, str, str]] = []

    def _nid(self, name: str) -> str:
        return f"{self.file}:{'.'.join(self.stack + [name])}"

    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        self._def(node, "method" if self.stack else "function")
        self.generic_visit(node)
        self.stack.pop()

    visit_AsyncFunctionDef = visit_FunctionDef

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        self._def(node, "class")
        self.generic_visit(node)
        self.stack.pop()

    def _def(self, node: ast.AST, kind: str) -> None:
        assert isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef))
        self.stack.append(node.name)
        nid = f"{self.file}:{'.'.join(self.stack)}"
        complexity = sum(isinstance(n, ast.stmt) for n in ast.walk(node))
        calls: list[str] = []
        for child in ast.walk(node):
            if isinstance(child, ast.Call):
                f = child.func
                if isinstance(f, ast.Name):
                    calls.append(f.id)
                elif isinstance(f, ast.Attribute):
                    calls.append(f.attr)
        self.nodes.append(Node(id=nid, name=node.name, kind=kind,
                               file=self.file, line=node.lineno,
                               calls=calls, complexity=max(1, complexity)))

    def visit_Call(self, node: ast.Call) -> None:
        if self.stack:
            src = f"{self.file}:{'.'.join(self.stack)}"
            f = node.func
            target = f.id if isinstance(f, ast.Name) else (
                f.attr if isinstance(f, ast.Attribute) else "")
            if target:
                self.edges.append((src, target, "calls"))
        self.generic_visit(node)


def _rel(path: Path, repo: Path) -> str:
    """Path relative to repo, whether path is absolute or repo-joined."""
    p = Path(path)
    r = Path(repo)
    try:
        return str(p.relative_to(r))
    except ValueError:
        pass
    try:
        return str(p.resolve().relative_to(r.resolve()))
    except (ValueError, OSError):
        return p.name


def parse_python_file(path: Path, repo: Path) -> tuple[list[Node], list[tuple[str, str, str]]]:
    rel = _rel(path, repo)
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"))
    except (SyntaxError, UnicodeDecodeError):
        return [], []
    v = _PyVisitor(rel)
    v.visit(tree)
    return v.nodes, v.edges


# ---------------------------------------------------- built-in TypeScript pass

_TS_DEF = re.compile(
    r"^\s*(?:export\s+)?(?:async\s+)?(?:function\s+(\w+)|class\s+(\w+)|"
    r"(?:const|let|var)\s+(\w+)\s*=\s*(?:async\s*)?\([^)]*\)\s*=>)")
_TS_METHOD = re.compile(r"^\s*(?:public|private|protected|async|\s)*(\w+)\s*\([^)]*\)\s*(?::\s*[^{]+)?\{")
_TS_IMPORT = re.compile(r"^\s*import\s+.*?from\s+['\"]([^'\"]+)['\"]")
_TS_CALL = re.compile(r"(\w+)\s*\(")
_TS_KW = {"if", "for", "while", "switch", "catch", "return", "function",
          "class", "import", "export", "new", "typeof", "await"}


def parse_ts_file(path: Path, repo: Path) -> tuple[list[Node], list[tuple[str, str, str]]]:
    rel = _rel(path, repo)
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        return [], []
    nodes: list[Node] = []
    edges: list[tuple[str, str, str]] = []
    current: Node | None = None
    for i, line in enumerate(lines, 1):
        m = _TS_DEF.match(line)
        if m:
            name = m.group(1) or m.group(2) or m.group(3) or ""
            kind = "class" if m.group(2) else "function"
            current = Node(id=f"{rel}:{name}", name=name, kind=kind,
                           file=rel, line=i)
            nodes.append(current)
            continue
        if current is None:
            m2 = _TS_IMPORT.match(line)
            if m2:
                edges.append((rel, m2.group(1), "imports"))
            continue
        for cm in _TS_CALL.finditer(line):
            if cm.group(1) not in _TS_KW:
                current.calls.append(cm.group(1))
                edges.append((current.id, cm.group(1), "calls"))
    for n in nodes:
        n.complexity = max(1, len(n.calls) + 1)
    if not nodes and lines:
        nodes.append(Node(id=f"{rel}:(module)", name=Path(rel).name,
                          kind="module", file=rel, line=1,
                          complexity=len(lines)))
    return nodes, edges


def build_repo_graph(repo: str | Path) -> Graph:
    """UA graph when present, else built-in pass over .py/.ts/.js/.tsx files."""
    repo = Path(repo)
    ua = find_ua_graph(repo)
    if ua is not None:
        return load_ua_graph(ua)
    g = Graph()
    for ext, parser in ((".py", parse_python_file), (".ts", parse_ts_file),
                        (".tsx", parse_ts_file), (".js", parse_ts_file)):
        for path in sorted(repo.rglob(f"*{ext}")):
            if ".git" in path.parts or "node_modules" in path.parts:
                continue
            nodes, edges = parser(path, repo)
            for n in nodes:
                g.add(n)
            g.edges.extend(edges)
    return g


def file_hash(path: str | Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()[:16]
