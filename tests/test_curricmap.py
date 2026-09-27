"""Curriculum mapping: modules crossed with course outcomes (F-174)."""
import json
import unittest

from groundwork import curricmap as mod
from groundwork import emoji as emojimod
from test_web import handler_for, make_module


def _concepts(db):
    from groundwork import db as dbmod
    con = dbmod.connect(db)
    try:
        return [(r["id"], r["name"], r["module_id"])
                for r in con.execute(
                    "SELECT id, name, module_id FROM concepts").fetchall()]
    finally:
        con.close()


def _own_first_concept(db):
    from groundwork import db as dbmod
    from groundwork import ownership as ownmod
    cid, _name, _mid = _concepts(db)[0]
    con = dbmod.connect(db)
    try:
        card = con.execute(
            "SELECT id FROM cards WHERE concept_id=? LIMIT 1",
            (cid,)).fetchone()[0]
        con.execute("UPDATE cards SET exercise_type=? WHERE id=?",
                    (ownmod.ownership_types()[0], card))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at) VALUES(?, 5, 4, '2026-09-20T10:00:00Z')",
                (card,))
        con.commit()
    finally:
        con.close()


def _spec(*concepts, title="Course 101"):
    return {"format": mod.FORMAT, "title": title,
            "outcomes": [{"id": "O1", "title": "First steps",
                          "concepts": list(concepts)}]}


class CurricmapUnitTest(unittest.TestCase):
    def test_parse_spec_dict_and_json(self):
        spec = _spec("a", "b")
        self.assertEqual(mod.parse_spec(spec)["outcomes"][0]["concepts"],
                         ["a", "b"])
        self.assertEqual(mod.parse_spec(json.dumps(spec))["title"],
                         "Course 101")

    def test_parse_spec_drops_blanks_dupes_and_empties(self):
        p = mod.parse_spec({"title": "t", "outcomes": [
            {"id": "O1", "concepts": ["a", "", "a", " b "]},
            {"id": "Ox", "concepts": ["", None]},
            "junk-row"]})
        self.assertEqual(len(p["outcomes"]), 1)
        self.assertEqual(p["outcomes"][0]["concepts"], ["a", "b"])

    def test_parse_spec_auto_id_and_garbage(self):
        p = mod.parse_spec({"outcomes": [{"concepts": ["a"]}]})
        self.assertEqual(p["outcomes"][0]["id"], "outcome-1")
        self.assertEqual(mod.parse_spec("{bad"), {"title": "", "outcomes": []})
        self.assertEqual(mod.parse_spec(None), {"title": "", "outcomes": []})
        self.assertEqual(mod.parse_spec(42), {"title": "", "outcomes": []})

    def test_matrix_view_coverage_and_missing(self):
        v = mod.matrix_view(
            _spec("a", "b", "ghost"),
            {"a": [("m1", True)], "b": [("m1", False), ("m2", False)]},
            {"m1": "Mod One", "m2": "Mod Two"})
        self.assertEqual((v["owned"], v["total"]), (1, 3))
        row = v["outcomes"][0]
        self.assertFalse(row["complete"])
        self.assertEqual(row["next"], "b")
        self.assertEqual(row["modules"],
                         [("m1", "Mod One", 1, 2), ("m2", "Mod Two", 0, 1)])
        ghost = [c for c in row["concepts"] if c["name"] == "ghost"][0]
        self.assertFalse(ghost["found"])

    def test_matrix_view_complete_and_hostile(self):
        v = mod.matrix_view(_spec("a"), {"a": [("m1", True)]}, {"m1": "M"})
        self.assertTrue(v["complete"])
        self.assertIsNone(v["outcomes"][0]["next"])
        v = mod.matrix_view(None, None, "junk")
        self.assertEqual((v["owned"], v["total"], v["outcomes"]), (0, 0, []))
        v = mod.matrix_view(_spec("a"), {"a": ["junk-hit", {"x": 1}]}, {})
        row = v["outcomes"][0]
        self.assertEqual((row["owned"], row["modules"]), (0, []))

    def test_matrix_table_renders_and_escapes(self):
        v = mod.matrix_view(_spec("a<script>", "b"),
                            {"a<script>": [("m1", True)]}, {"m1": "M"})
        out = mod.matrix_table(v)
        self.assertIn("id='curricmap'", out)
        self.assertIn("1 of 2 outcome concepts owned", out)
        self.assertIn("Not in library: b", out)
        self.assertNotIn("<script>", out)
        self.assertNotIn("leaderboard", out.casefold())

    def test_matrix_table_empty_without_rows(self):
        self.assertEqual(mod.matrix_table({}), "")
        self.assertEqual(mod.matrix_table(None), "")
        self.assertEqual(mod.matrix_table({"outcomes": []}), "")
        self.assertEqual(mod.matrix_table("junk"), "")

    def test_library_index_lists_names_unowned(self):
        _tmp, db, _server, _out = make_module("curric index mod")
        _cid, name, mid = _concepts(db)[0]
        index, titles = mod.library_index(db)
        self.assertIn(name, index)
        self.assertFalse(any(flag for _m, flag in index[name]))
        self.assertIn(mid, titles)

    def test_matrix_html_empty_without_spec(self):
        _tmp, db, _server, _out = make_module("curric empty mod")
        self.assertEqual(mod.matrix_html(db, ""), "")
        self.assertEqual(mod.matrix_html(db, None), "")
        self.assertEqual(mod.matrix_html(db, "not json"), "")
        self.assertEqual(mod.matrix_html(db, json.dumps({"title": "t"})), "")


class CurricmapEffectTest(unittest.TestCase):
    def test_library_page_without_curriculum_is_legacy(self):
        _tmp, db, _server, _out = make_module("curric legacy mod")
        h = handler_for(db)
        body = h.modules_html()
        self.assertNotIn("id='curricmap'", body)
        self.assertEqual(h.modules_html(curriculum=""), body)
        self.assertEqual(h.modules_html(curriculum="not json"), body)
        self.assertEqual(h.modules_html(curriculum=None), body)

    def test_library_page_with_curriculum_renders_matrix(self):
        _tmp, db, _server, out = make_module("curric live mod")
        _cid, name, _mid = _concepts(db)[0]
        body = handler_for(db).modules_html(
            curriculum=json.dumps(_spec(name, "ghost-concept")))
        self.assertIn("id='curricmap'", body)
        self.assertIn("First steps", body)
        self.assertIn("0 of 2 outcome concepts owned", body)
        self.assertIn("Not in library: ghost-concept", body)
        self.assertIn(f"Next: {name}", body)
        self.assertIn(f"/modules/{out['module_id']}", body)

    def test_library_matrix_marks_owned_complete(self):
        _tmp, db, _server, _out = make_module("curric owned mod")
        _own_first_concept(db)
        _cid, name, _mid = _concepts(db)[0]
        body = handler_for(db).modules_html(
            curriculum=json.dumps(_spec(name)))
        self.assertIn("1 of 1 outcome concepts owned", body)
        self.assertIn("curriculum complete", body)


class CurricmapShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])

    def test_source_is_plain_ascii(self):
        import pathlib
        pathlib.Path(mod.__file__).read_bytes().decode("ascii")


if __name__ == "__main__":
    unittest.main()
