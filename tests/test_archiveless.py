"""Retired-lesson archive (I-150)."""
import unittest

from groundwork import archiveless as mod

from test_web import handler_for, make_module


def _row(cid="m:add", name="add", file="calc.py"):
    return {"cid": cid, "name": name, "file": file, "line": 1}


class ReasonTest(unittest.TestCase):
    def test_live_lesson_has_no_reason(self):
        import tempfile
        tmp = tempfile.mkdtemp(prefix="gw-alive-")
        open(f"{tmp}/calc.py", "w").write("x = 1\n")
        self.assertEqual(
            mod.reason_for("add", "calc.py", tmp, True), "")

    def test_deleted_file_retires(self):
        self.assertEqual(
            mod.reason_for("add", "gone.py", "/tmp", True),
            "source file deleted")

    def test_cardless_concept_retires(self):
        self.assertEqual(
            mod.reason_for("add", "calc.py", "", False),
            "no cards — retired by regeneration")

    def test_hostile_never_raises(self):
        self.assertEqual(mod.reason_for(None, None, None, True), "")
        self.assertEqual(mod.retired_for(None), [])
        self.assertEqual(mod.archive_html("nope"), "")
        self.assertEqual(mod.repo_of({}), "")


class ArchiveTest(unittest.TestCase):
    def test_retired_for_names_reasons(self):
        rows = [_row("m:a", "a", "calc.py"), _row("m:b", "b", "calc.py")]
        out = mod.retired_for(rows, {"m:a": [], "m:b": [{"id": "c"}]}, "")
        self.assertEqual([(e["name"], e["reason"]) for e in out],
                         [("a", "no cards — retired by regeneration")])

    def test_archive_section_shape(self):
        body = mod.archive_html([{"name": "a", "reason": "r"}])
        self.assertIn("Retired lessons", body)
        self.assertIn("a", body)
        self.assertEqual(mod.archive_html([]), "")

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_live_module_has_no_archive(self):
        _tmp, db, _s, out = make_module("archiveless caller")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("Retired lessons</h3>", body)

    def test_module_page_shows_archive(self):
        # Retire the fixture concept by deleting its cards: the
        # module page grows an archive section naming it.
        from groundwork import db as dbmod
        _tmp, db, _s, out = make_module("archiveless shows")
        con = dbmod.connect(db)
        try:
            con.execute("DELETE FROM cards")
            con.commit()
        finally:
            con.close()
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("class='archive'", body)
        self.assertIn("no cards — retired by regeneration", body)


if __name__ == "__main__":
    unittest.main()
