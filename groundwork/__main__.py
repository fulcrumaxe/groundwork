"""Groundwork CLI: init, serve, mcp, check-stale, e2e. One-command self-host."""
from __future__ import annotations

import argparse
import sys


def cmd_init(args) -> int:
    from . import db as dbmod
    dbmod.init_db(args.db)
    print(f"initialized {args.db}")
    return 0


def cmd_serve(args) -> int:
    from . import web as webmod
    webmod.serve(args.host, args.port, args.db)
    return 0


def cmd_mcp(args) -> int:
    from . import mcp as mcplib
    mcplib.serve_stdio(args.db)
    return 0


def cmd_stale(args) -> int:
    from . import web as webmod
    n = webmod.check_stale(args.db, args.repo)
    print(f"{n} stale card(s)")
    return 0


def cmd_export_module(args) -> int:
    import json
    from . import share as sharemod
    try:
        doc = sharemod.export_module(args.db, args.module)
    except KeyError as e:
        print(f"error: {e}")
        return 1
    text = json.dumps(doc, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"exported {args.module} -> {args.out}")
    else:
        print(text)
    return 0


def cmd_import_module(args) -> int:
    import json
    from . import share as sharemod
    with open(args.src, encoding="utf-8") as f:
        doc = json.load(f)
    try:
        out = sharemod.import_module(args.db, doc)
    except ValueError as e:
        print(f"error: {e}")
        return 1
    print(f"{out['status']}: {out['module_id']} "
          f"({out['concepts']} concepts, {out['cards']} cards)")
    return 0


def cmd_export_seed(args) -> int:
    """Every module under one repo, relabeled to the portable seed name."""
    import json
    from . import share as sharemod
    doc = sharemod.export_seed(args.db, args.repo)
    text = json.dumps(doc, indent=2)
    if args.out:
        with open(args.out, "w", encoding="utf-8") as f:
            f.write(text)
        print(f"exported seed {doc['repo']} -> {args.out} "
              f"({len(doc['modules'])} modules)")
    else:
        print(text)
    return 0


def cmd_import_seed(args) -> int:
    """Load a seed file (or single module); duplicates skip cleanly."""
    import json
    from . import share as sharemod
    with open(args.src, encoding="utf-8") as f:
        doc = json.load(f)
    try:
        out = sharemod.import_seed(args.db, doc, args.as_repo)
    except ValueError as e:
        print(f"error: {e}")
        return 1
    for r in out:
        print(f"{r['status']}: {r['module_id']} "
              f"({r['concepts']} concepts, {r['cards']} cards)")
    return 0


def cmd_docs(args) -> int:
    from . import docs as docsmod
    changed = docsmod.render_all()
    if args.check:
        if changed:
            print("docs stale: " + ", ".join(changed))
            return 1
        print("docs fresh")
        return 0
    print("wrote: " + ", ".join(changed) if changed else "docs fresh")
    return 0


def cmd_e2e(args) -> int:
    import json
    import subprocess
    import tempfile
    from pathlib import Path
    from . import db as dbmod
    from . import mcp as mcplib

    tmp = Path(tempfile.mkdtemp(prefix="gw-e2e-"))
    (tmp / "calc.py").write_text(
        "def add(a=2, b=3):\n    total = a + b\n    return total\n\n"
        "def greet(name='world'):\n    msg = 'hi ' + name\n    return msg\n", encoding="utf-8")
    subprocess.run(["git", "-C", str(tmp), "init", "-q"], check=False)
    subprocess.run(["git", "-C", str(tmp), "add", "."], check=False)
    db_path = tmp / "e2e.db"
    server = mcplib.MCPServer(db_path)
    out = server.tool_create_learning_module({
        "repo_path": str(tmp), "task_summary": "E2E: calc helpers",
        "learner_level": "beginner"})
    print(json.dumps({k: v for k, v in out.items() if k != "exercises"}, indent=2))
    ok = out["pass_rate"] >= 0.9 and out["exercise_count"] > 0
    # Review cycle: answer every due card correctly from its back/payload.
    con = dbmod.connect(db_path)
    try:
        cards = con.execute("SELECT * FROM cards").fetchall()
    finally:
        con.close()
    for c in cards:
        p = json.loads(c["payload"] or "{}")
        t = int(c["exercise_type"])
        if t == 1:
            ans = "5"
        elif t == 2:
            blanks = p.get("blanks") or [{"id": 0, "answers": p.get("answers", [""])}]
            ans = "\n".join(f"{b['id']}={(b.get('answers') or [''])[0]}"
                            for b in blanks)
        elif t == 3:
            ans = p.get("signature", "")
        elif t == 4:
            ans = p.get("answer", "")
        elif t in (5, 6, 24, 25):
            ans = " ".join(p.get("rubric", []))
        elif t == 21:
            ans = f"{p.get('bug_line', '')} " + " ".join(p.get("rubric", []))
        elif t == 22:
            ans = p.get("answer", "") + "\njustified by the reference behavior"
        elif t == 8:
            ans = p.get("expected", "")
        elif t == 9:
            ans = "\n".join(str(x) for x in p.get("expected", []))
        elif t in (7, 15, 16, 18):
            ans = p.get("answer", "")
        elif t == 17:
            ans = (f"{p.get('target', 'x')}_renamed "
                   + " ".join(p.get("rubric", [])))
        elif t == 29:
            ans = "\n".join(f"{it['id']}={it['level']}"
                            for it in p.get("checklist", []))
        elif t == 32:
            ans = f">>> {p.get('call', '')}\n{p.get('expected', '')}"
        elif t in (10, 11):
            ans = " ".join(str(i) for i in range(len(p.get("lines", []))))
            # order indices refer to shuffled list; solve via solution match
            sol, lines = p.get("solution", []), p.get("lines", [])
            ans = " ".join(str(lines.index(l)) for l in sol if l in lines)
        elif t in (12, 19, 23, 27, 28, 31):
            ans = p.get("reference", "")
        elif t == 20:
            # Satisfy the extension requirement: append the optional
            # parameter to a single-line reference signature.
            ans = p.get("reference", "")
            lines = ans.splitlines()
            first = lines[0].rstrip() if lines else ""
            if first.endswith("):") and "strict" not in first:
                base = first[:-2]
                sep = "" if base.endswith("(") else ", "
                lines[0] = f"{base}{sep}strict=False):"
                ans = "\n".join(lines)
        elif t == 13:
            ans = str(p.get("bug_line", ""))
        elif t == 30:
            ans = "\n".join(f"{k}={v}" for k, v in p.get("key", {}).items())
        elif t == 14:
            ans = p.get("fixed", "")
        else:
            ans = ""
        r = server.submit_review(c["id"], ans, 4)
        assert r["result"]["pass"], f"card {c['id']} type {t} failed: {r['result']}"
    due = server.tool_list_due_reviews({"limit": 50})["count"]
    print(f"reviewed {len(cards)} cards, {due} still due (spaced out)")
    print("E2E " + ("PASS" if ok else "FAIL"))
    return 0 if ok else 1


def cmd_review(ns) -> int:
    """Terminal review loop: due cards, stdin answers, verdicts."""
    from . import mcp as mcplib
    server = mcplib.MCPServer(ns.db)
    due = server.tool_list_due_reviews({"limit": ns.limit})["due"]
    if not due:
        print("Nothing due — enjoy the calm.")
        return 0
    done = 0
    for c in due:
        print(f"\n[{c.get('concept', '?')}] {c.get('front', '')}")
        try:
            ans = input("Your answer (q to quit): ")
        except EOFError:
            break
        if ans.strip().lower() in ("q", "quit", "exit"):
            break
        try:
            conf = (input("Confidence 1-5 [3]: ").strip() or "3")
        except EOFError:
            conf = "3"
        try:
            conf_i = int(conf)
        except ValueError:
            conf_i = 3
        out = server.submit_review(c["id"], ans, conf_i)
        res = out.get("result", {})
        mark = "PASS" if res.get("pass") else "FAIL"
        print(f"{mark}: {res.get('feedback', '')}")
        done += 1
    print(f"\nReviewed {done} card(s).")
    return 0


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="groundwork", description="Code learning companion")
    ap.add_argument("--db", default="groundwork.db")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("init").set_defaults(fn=cmd_init)
    rv = sub.add_parser("review"); rv.add_argument("--limit", type=int, default=20)
    rv.set_defaults(fn=cmd_review)
    s = sub.add_parser("serve"); s.add_argument("--host", default="127.0.0.1")
    s.add_argument("--port", type=int, default=8765); s.set_defaults(fn=cmd_serve)
    sub.add_parser("mcp").set_defaults(fn=cmd_mcp)
    st = sub.add_parser("check-stale"); st.add_argument("--repo", default=".")
    st.set_defaults(fn=cmd_stale)
    sub.add_parser("e2e").set_defaults(fn=cmd_e2e)
    ex = sub.add_parser("export-module")
    ex.add_argument("--module", required=True)
    ex.add_argument("--out", default="")
    ex.set_defaults(fn=cmd_export_module)
    im = sub.add_parser("import-module")
    im.add_argument("--in", dest="src", required=True)
    im.set_defaults(fn=cmd_import_module)
    es = sub.add_parser("export-seed")
    es.add_argument("--repo", default=".")
    es.add_argument("--out", default="")
    es.set_defaults(fn=cmd_export_seed)
    isn = sub.add_parser("import-seed")
    isn.add_argument("--in", dest="src", required=True)
    isn.add_argument("--as-repo", default="")
    isn.set_defaults(fn=cmd_import_seed)
    dc = sub.add_parser("docs")
    dc.add_argument("--check", action="store_true")
    dc.set_defaults(fn=cmd_docs)
    args = ap.parse_args(argv)
    return args.fn(args)


if __name__ == "__main__":
    sys.exit(main())
