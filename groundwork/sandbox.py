"""Sandbox runner + verification gate (PRD pipeline step 5).

Runs Python via subprocess with timeout + cwd jail; TypeScript/JavaScript
via `node` when available. Discards exercises whose answers don't reproduce.
"""
from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class RunResult:
    ok: bool
    stdout: str = ""
    stderr: str = ""
    data: list = field(default_factory=list)


class SandboxRunner:
    def __init__(self, timeout: int = 10):
        self.timeout = timeout
        self.node = shutil.which("node")

    def run_python(self, code: str) -> RunResult:
        with tempfile.TemporaryDirectory(prefix="gw-") as tmp:
            try:
                proc = subprocess.run(
                    [sys.executable, "-c", code], capture_output=True,
                    text=True, timeout=self.timeout, cwd=tmp)
            except subprocess.TimeoutExpired:
                return RunResult(False, "", "timeout")
            return RunResult(proc.returncode == 0, proc.stdout, proc.stderr)

    def trace_python(self, code: str, var: str) -> RunResult:
        """Instrumented execution: record `var` at each step.

        Code runs inside a helper call so line events fire reliably;
        values are captured before each line and on return (post-state).
        """
        import textwrap
        tracer = (
            "import sys\n"
            f"_vals=[]\n_var={var!r}\n"
            "def _t(frame,event,arg):\n"
            "  global _vals\n"
            "  if event in ('line','return'):\n"
            "    try:_vals.append(repr(frame.f_locals.get(_var,'<undef>')))\n"
            "    except Exception:_vals.append('<err>')\n"
            "  return _t\n"
            "def _run():\n" + textwrap.indent(code, "  ") + "\n"
            "sys.settrace(_t)\n"
            "try:\n  _run()\n"
            "finally:\n  sys.settrace(None)\n"
            "print('GWTRACE:'+repr(_vals[1:]))\n"
        )
        res = self.run_python(tracer)
        if not res.ok:
            return res
        data: list = []
        for line in res.stdout.splitlines():
            if line.startswith("GWTRACE:"):
                try:
                    import ast as _ast
                    data = [str(x) for x in _ast.literal_eval(line[8:])]
                except (SyntaxError, ValueError):
                    pass
        res.data = data
        return res

    def run(self, code: str, lang: str = "python") -> RunResult:
        if lang in ("ts", "typescript", "js", "javascript"):
            return self.run_node(code)
        return self.run_python(code)

    def trace(self, code: str, var: str) -> RunResult:
        return self.trace_python(code, var)

    def check_ts(self, code: str) -> RunResult:
        if not self.node:
            return RunResult(False, "", "node not installed")
        with tempfile.TemporaryDirectory(prefix="gw-") as tmp:
            f = Path(tmp) / "snippet.mjs"
            f.write_text(code, encoding="utf-8")
            try:
                proc = subprocess.run([self.node, "--check", str(f)],
                                      capture_output=True, text=True,
                                      timeout=self.timeout, cwd=tmp)
            except subprocess.TimeoutExpired:
                return RunResult(False, "", "timeout")
            return RunResult(proc.returncode == 0, proc.stdout, proc.stderr)

    def run_node(self, code: str) -> RunResult:
        if not self.node:
            return RunResult(False, "", "node not installed")
        with tempfile.TemporaryDirectory(prefix="gw-") as tmp:
            try:
                proc = subprocess.run([self.node, "-e", code], capture_output=True,
                                      text=True, timeout=self.timeout, cwd=tmp)
            except subprocess.TimeoutExpired:
                return RunResult(False, "", "timeout")
            return RunResult(proc.returncode == 0, proc.stdout, proc.stderr)


def _parses(code: str, runner: SandboxRunner) -> bool:
    """True if the code parses as Python (or passes node --check for JS/TS)."""
    import ast as _ast
    if not code.strip():
        return False
    try:
        _ast.parse(code)
        return True
    except SyntaxError:
        pass
    if runner.node and any(k in code for k in ("function ", "=>", "const ", "let ", "import ")):
        return runner.check_ts(code).ok
    return False


def verify_module(exercises: list[dict], runner: SandboxRunner | None = None) -> dict:
    """Run every executable exercise; discard unverifiable items.

    Returns {kept, dropped, pass_rate}.
    """
    runner = runner or SandboxRunner()
    kept, dropped = [], []
    for ex in exercises:
        t, p = ex.get("type"), ex.get("payload", {})
        try:
            if t == 8:
                res = runner.run(p.get("code", ""))
                good = res.ok and res.stdout.strip() == p.get("expected", "").strip()
            elif t == 9:
                res = runner.trace(p.get("code", ""), p.get("var", ""))
                good = res.ok and (not p.get("expected") or res.data == p["expected"])
            elif t == 11:
                code = p.get("solution", [])
                code = "\n".join(code) if isinstance(code, list) else code
                tests = p.get("tests", "")
                if tests:
                    res = runner.run(code + "\n" + tests)
                    good = res.ok and "FAIL" not in res.stdout
                else:
                    # No harness: ordering real code is verifiable by exact
                    # order match; the shown slice need not parse alone as
                    # long as the full block it came from does.
                    good = (_parses(code, runner)
                            or _parses(p.get("code_block", ""), runner))
            elif t in (12, 19, 20, 23):
                code = p.get("reference", "")
                res = runner.run(code + "\n" + p.get("tests", ""))
                good = res.ok and "FAIL" not in res.stdout
            elif t == 14:
                # Keep only if buggy fails and fixed passes the same tests.
                bad = runner.run(p.get("buggy", "") + "\n" + p.get("tests", ""))
                good_r = runner.run(p.get("fixed", "") + "\n" + p.get("tests", ""))
                good = ((not bad.ok or "FAIL" in bad.stdout) and good_r.ok
                        and "FAIL" not in good_r.stdout)
            else:
                good = bool(ex.get("front"))  # non-executable: schema check
            (kept if good else dropped).append(ex)
        except Exception:
            dropped.append(ex)
    total = max(1, len(exercises))
    return {"kept": kept, "dropped": dropped, "pass_rate": len(kept) / total}
