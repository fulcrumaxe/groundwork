"""Module sharing: export carries teaching content, never reviews."""
import json
import tempfile
import unittest
from pathlib import Path

from groundwork import db as dbmod
from groundwork import share as sharemod

from test_web import make_module


class ShareRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("share mod")
        self.mid = self.out["module_id"]
        card = self.server.tool_list_due_reviews({"limit": 1})["due"][0]
        self.server.submit_review(card["id"], "5", 4)

    def test_export_then_import_into_fresh_db(self):
        doc = sharemod.export_module(self.db, self.mid)
        self.assertEqual(doc["format"], "groundwork-module/1")
        self.assertGreater(len(doc["concepts"]), 0)
        self.assertGreater(len(doc["cards"]), 0)
        other = str(Path(tempfile.mkdtemp(prefix="gw-share-")) / "other.db")
        out = sharemod.import_module(other, doc)
        self.assertEqual(out["status"], "imported")
        con = dbmod.connect(other)
        try:
            got = con.execute("SELECT task_summary FROM modules WHERE id=?",
                              (self.mid,)).fetchone()
            self.assertIsNotNone(got)
            reviews = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
            self.assertEqual(reviews, 0)
            due = con.execute(
                "SELECT COUNT(*) FROM cards WHERE due <= "
                "strftime('%Y-%m-%dT%H:%M:%SZ','now')").fetchone()[0]
            self.assertGreater(due, 0)
        finally:
            con.close()

    def test_reimport_is_skipped_duplicate(self):
        doc = sharemod.export_module(self.db, self.mid)
        other = str(Path(tempfile.mkdtemp(prefix="gw-share-")) / "dup.db")
        first = sharemod.import_module(other, doc)
        second = sharemod.import_module(other, doc)
        self.assertEqual(first["status"], "imported")
        self.assertEqual(second["status"], "skipped-duplicate")

    def test_export_unknown_module_raises(self):
        with self.assertRaises(KeyError):
            sharemod.export_module(self.db, "nope")

    def test_import_rejects_foreign_format(self):
        other = str(Path(tempfile.mkdtemp(prefix="gw-share-")) / "bad.db")
        with self.assertRaises(ValueError):
            sharemod.import_module(other, {"format": "nope"})

    def test_shared_json_survives_disk(self):
        doc = sharemod.export_module(self.db, self.mid)
        path = Path(tempfile.mkdtemp(prefix="gw-share-")) / "share.json"
        path.write_text(json.dumps(doc), encoding="utf-8")
        other = str(path.parent / "disk.db")
        out = sharemod.import_module(other, json.loads(path.read_text()))
        self.assertEqual(out["status"], "imported")


class SeedRoundTripTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("seed mod")
        self.mid = self.out["module_id"]

    def test_export_seed_collects_repo_modules(self):
        doc = sharemod.export_seed(self.db, str(self.tmp))
        self.assertEqual(doc["format"], "groundwork-seed/1")
        self.assertEqual(doc["repo"], "groundwork")
        self.assertEqual(len(doc["modules"]), 1)
        self.assertEqual(doc["modules"][0]["module"]["repo"], "groundwork")

    def test_export_seed_ignores_other_repos(self):
        doc = sharemod.export_seed(self.db, "/elsewhere")
        self.assertEqual(doc["modules"], [])

    def test_import_seed_into_fresh_db_then_skips(self):
        doc = sharemod.export_seed(self.db, str(self.tmp))
        other = str(Path(tempfile.mkdtemp(prefix="gw-seed-")) / "seed.db")
        first = sharemod.import_seed(other, doc)
        self.assertEqual(first[0]["status"], "imported")
        con = dbmod.connect(other)
        try:
            reviews = con.execute("SELECT COUNT(*) FROM reviews").fetchone()[0]
            self.assertEqual(reviews, 0)
        finally:
            con.close()
        second = sharemod.import_seed(other, doc)
        self.assertEqual(second[0]["status"], "skipped-duplicate")

    def test_import_seed_accepts_single_module_and_relabel(self):
        doc = sharemod.export_module(self.db, self.mid)
        other = str(Path(tempfile.mkdtemp(prefix="gw-seed-")) / "one.db")
        out = sharemod.import_seed(other, doc, relabel_repo="/mine")
        self.assertEqual(out[0]["status"], "imported")
        con = dbmod.connect(other)
        try:
            repo = con.execute("SELECT repo FROM modules WHERE id=?",
                               (self.mid,)).fetchone()[0]
            self.assertEqual(repo, "/mine")
        finally:
            con.close()

    def test_import_seed_rejects_foreign_format(self):
        other = str(Path(tempfile.mkdtemp(prefix="gw-seed-")) / "bad.db")
        with self.assertRaises(ValueError):
            sharemod.import_seed(other, {"format": "nope"})


if __name__ == "__main__":
    unittest.main()
