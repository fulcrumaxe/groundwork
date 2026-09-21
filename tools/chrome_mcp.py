#!/usr/bin/env python3
"""Stdio client for the Chrome DevTools MCP server (chrome-devtools-mcp).

Same server other projects on this machine drive via `mcp__chrome-devtools__*`
tools; this client speaks the same MCP JSON-RPC over stdio so the browser
verification sweep runs reproducibly from `nix run .#chrome-verify`
without any editor MCP plumbing.

Executable resolution (first hit wins):
- `CHROME_MCP_BIN`: full path to the chrome-devtools-mcp server js
  (e.g. a nix-provided binary).
- otherwise `npx -y chrome-devtools-mcp@1.9.0` (pinned; npm caches it
  after the first fetch so later runs work offline).

The browser under test resolves via `CHROME_EXECUTABLE`, else whatever
`chromium` / `google-chrome` is on PATH (the flake provides chromium).

CLI:
    tools/chrome_mcp.py <tool> '<json-args>' [--timeout SECS]
    tools/chrome_mcp.py __tools__
"""
from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import threading
import time

MCP_PACKAGE = "chrome-devtools-mcp@1.9.0"


def _resolve_server_cmd() -> list[str]:
    explicit = os.environ.get("CHROME_MCP_BIN")
    if explicit:
        return ["node", explicit]
    return ["npx", "-y", MCP_PACKAGE]


def _resolve_chrome() -> str | None:
    explicit = os.environ.get("CHROME_EXECUTABLE")
    if explicit:
        return explicit
    for name in ("chromium", "google-chrome", "google-chrome-stable"):
        found = shutil.which(name)
        if found:
            return found
    return None


class MCPClient:
    """One MCP session (one browser). Close pages when done — tabs
    persist for the server's lifetime and keep page timers firing."""

    def __init__(self, roots: list[str] | None = None):
        self._roots = [os.path.abspath(r) for r in (roots or [])]
        cmd = _resolve_server_cmd() + [
            "--headless", "--isolated",
            "--no-usage-statistics", "--no-performance-crux",
            "--screenshotFormat", "jpeg", "--screenshotQuality", "60",
            "--screenshotMaxWidth", "1100",
        ]
        chrome = _resolve_chrome()
        if chrome:
            cmd += ["--executablePath", chrome]
        env = {**os.environ, "CI": "1"}
        self.proc = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL, text=True, bufsize=1, env=env)
        self._id = 0
        self._buf: list = []
        self._cond = threading.Condition()
        self._wlock = threading.Lock()
        threading.Thread(target=self._reader, daemon=True).start()
        self._request("initialize", {
            "protocolVersion": "2024-11-05",
            "capabilities": {"roots": {"listChanged": False}},
            "clientInfo": {"name": "chrome-verify", "version": "0.1"}})
        self._notify("notifications/initialized", {})

    def _reader(self):
        try:
            for line in self.proc.stdout:
                line = line.strip()
                if not line:
                    continue
                try:
                    msg = json.loads(line)
                except json.JSONDecodeError:
                    continue
                if "method" in msg and "id" in msg:
                    self._answer_server_request(msg)
                    continue
                with self._cond:
                    self._buf.append(msg)
                    self._cond.notify_all()
        except Exception:
            pass

    def _answer_server_request(self, msg) -> None:
        """Answer server->client requests (e.g. roots/list for file sandbox)."""
        method, rid = msg.get("method"), msg.get("id")
        if method == "roots/list":
            result = {"roots": [
                {"uri": f"file://{r}", "name": os.path.basename(r) or r}
                for r in self._roots]}
        else:
            result = {}
        try:
            self._write({"jsonrpc": "2.0", "id": rid, "result": result})
        except Exception:
            pass

    def _write(self, obj) -> None:
        with self._wlock:
            self.proc.stdin.write(json.dumps(obj) + "\n")
            self.proc.stdin.flush()

    def _request(self, method, params, timeout=120):
        self._id += 1
        rid = self._id
        req = {"jsonrpc": "2.0", "id": rid, "method": method}
        if params is not None:
            req["params"] = params
        self._write(req)
        deadline = time.time() + timeout
        with self._cond:
            while True:
                for i, m in enumerate(self._buf):
                    if m.get("id") == rid:
                        self._buf.pop(i)
                        if "error" in m:
                            raise RuntimeError(json.dumps(m["error"])[:2000])
                        return m.get("result")
                remaining = deadline - time.time()
                if remaining <= 0:
                    raise TimeoutError(f"mcp {method} timed out")
                self._cond.wait(timeout=min(remaining, 5))

    def _notify(self, method, params):
        self._write({"jsonrpc": "2.0", "method": method, "params": params})

    def call(self, tool, args=None, timeout=120):
        return self._request("tools/call",
                             {"name": tool, "arguments": args or {}},
                             timeout=timeout)

    def tools(self):
        return self._request("tools/list", {})

    def close(self):
        try:
            self.proc.terminate()
        except Exception:
            pass


def main(argv: list[str]) -> int:
    tool = argv[1]
    args = json.loads(argv[2]) if len(argv) > 2 else {}
    timeout = 120
    if "--timeout" in argv:
        timeout = int(argv[argv.index("--timeout") + 1])
    client = MCPClient()
    try:
        if tool == "__tools__":
            print(json.dumps(
                [t["name"] for t in client.tools()["tools"]], indent=1))
        else:
            print(json.dumps(client.call(tool, args, timeout),
                             indent=1)[:6000])
        return 0
    finally:
        client.close()


if __name__ == "__main__":
    sys.exit(main(sys.argv))
