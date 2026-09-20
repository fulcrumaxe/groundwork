"""F-362/F-364 integration files: pre-commit hook and CI workflow."""
import os
import shutil
import sqlite3
import subprocess
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def hook_env(db):
    path = os.environ.get("PATH", "/usr/bin:/bin")
    gitdir = os.path.dirname(shutil.which("git") or "/usr/bin/git")
    return {"PATH": f"{gitdir}:/usr/bin:/bin:{path}", "GW_DB": db}


def seed_db(db, proven: bool):
    con = sqlite3.connect(db)
    try:
        con.execute("CREATE TABLE concepts(id TEXT PRIMARY KEY, module_id TEXT,"
                    " name TEXT, file TEXT)")
        con.execute("CREATE TABLE cards(id TEXT PRIMARY KEY, concept_id TEXT,"
                    " exercise_type TEXT)")
        con.execute("CREATE TABLE reviews(id INTEGER PRIMARY KEY AUTOINCREMENT,"
                    " card_id TEXT, grade INTEGER, confidence INTEGER DEFAULT 3)")
        con.execute("INSERT INTO concepts VALUES('m:c','m','c','a.py')")
        con.execute("INSERT INTO cards VALUES('m:c:ex001','m:c','1')")
        if proven:
            con.execute("INSERT INTO reviews(card_id, grade) VALUES('m:c:ex001',5)")
        con.commit()
    finally:
        con.close()


def make_staged_repo():
    tmp = Path(tempfile.mkdtemp(prefix="gw-hook-"))
    subprocess.run(["git", "init", "-q", str(tmp)], check=True)
    subprocess.run(["git", "-C", str(tmp), "config", "user.email", "t@t"],
                   check=True)
    subprocess.run(["git", "-C", str(tmp), "config", "user.name", "t"],
                   check=True)
    (tmp / "a.py").write_text("x = 1\n")
    subprocess.run(["git", "-C", str(tmp), "add", "a.py"], check=True)
    return tmp


class HookTest(unittest.TestCase):
    def test_warns_on_unproven_never_blocks(self):
        tmp = make_staged_repo()
        db = str(tmp / "gw.db")
        seed_db(db, proven=False)
        env = hook_env(db)
        r = subprocess.run(["sh", str(ROOT / "hooks" / "pre-commit")],
                           capture_output=True, text=True, cwd=tmp, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertIn("unproven concept", r.stdout)
        self.assertIn("a.py", r.stdout)

    def test_silent_when_proven(self):
        tmp = make_staged_repo()
        db = str(tmp / "gw.db")
        seed_db(db, proven=True)
        env = hook_env(db)
        r = subprocess.run(["sh", str(ROOT / "hooks" / "pre-commit")],
                           capture_output=True, text=True, cwd=tmp, env=env)
        self.assertEqual(r.returncode, 0)
        self.assertNotIn("unproven concept", r.stdout)

    def test_no_db_no_crash(self):
        tmp = make_staged_repo()
        env = hook_env(str(tmp / "missing.db"))
        r = subprocess.run(["sh", str(ROOT / "hooks" / "pre-commit")],
                           capture_output=True, text=True, cwd=tmp, env=env)
        self.assertEqual(r.returncode, 0)


class WorkflowTest(unittest.TestCase):
    def test_groundwork_workflow_markers(self):
        wf = (ROOT / ".github" / "workflows" / "groundwork.yml").read_text()
        for marker in ("python -m unittest discover -s tests",
                       "python -m groundwork e2e",
                       "create_learning_module",
                       "upload-artifact"):
            self.assertIn(marker, wf)


if __name__ == "__main__":
    unittest.main()
