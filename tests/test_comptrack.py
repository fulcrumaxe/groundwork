"""Compliance tracks: required concepts verified against owned proofs (F-189)."""
import json
import unittest

from groundwork import comptrack as mod
from groundwork import emoji as emojimod
from test_web import handler_for, make_module


def _concepts(db):
    from groundwork import db as dbmod
    con = dbmod.connect(db)
    try:
        return [(r["id"], r["name"])
                for r in con.execute("SELECT id, name FROM concepts").fetchall()]
    finally:
        con.close()


class ComptrackUnitTest(unittest.TestCase):
    def test_parse_spec_dict_and_json(self):
        spec = {"format": mod.FORMAT, "title": "Q3", "required": ["a", "b"]}
        self.assertEqual(mod.parse_spec(spec)["required"], ["a", "b"])
        self.assertEqual(mod.parse_spec(json.dumps(spec))["title"], "Q3")

    def test_parse_spec_drops_blanks_and_dupes(self):
        p = mod.parse_spec({"title": "t", "required": ["a", "", "a", " b "]})
        self.assertEqual(p["required"], ["a", "b"])

    def test_parse_spec_garbage_is_empty(self):
        self.assertEqual(mod.parse_spec("{bad"), {"title": "", "required": []})
        self.assertEqual(mod.parse_spec(None), {"title": "", "required": []})
        self.assertEqual(mod.parse_spec(42), {"title": "", "required": []})

    def test_comply_view_verification(self):
        v = mod.comply_view({"title": "t", "required": ["a", "b"]}, owned={"a"})
        self.assertEqual((v["verified"], v["total"]), (1, 2))
        self.assertEqual(v["next"], "b")
        self.assertFalse(v["passed"])

    def test_comply_view_mastery_counts_at_threshold(self):
        v = mod.comply_view({"required": ["a"]}, mastery_of={"a": 0.9})
        self.assertTrue(v["passed"])
        v = mod.comply_view({"required": ["a"]}, mastery_of={"a": 0.5})
        self.assertFalse(v["passed"])

    def test_comply_view_hostile(self):
        v = mod.comply_view(None, owned=None, mastery_of="junk")
        self.assertEqual((v["total"], v["next"]), (0, None))

    def test_verify_html_renders_and_escapes(self):
        out = mod.verify_html({"title": "t", "required": ["a<script>", "b"]},
                              owned={"a<script>"})
        self.assertIn("id='comptrack'", out)
        self.assertIn("comply-verified", out)
        self.assertIn("comply-pending", out)
        self.assertNotIn("<script>", out)
        self.assertNotIn("checkbox", out.casefold())

    def test_verify_html_empty_without_spec(self):
        self.assertEqual(mod.verify_html(None), "")
        self.assertEqual(mod.verify_html({}), "")
        self.assertEqual(mod.verify_html("not json"), "")


class ComptrackEffectTest(unittest.TestCase):
    def test_module_page_without_comply_is_legacy(self):
        _tmp, db, _server, out = make_module("comply legacy mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("id='comptrack'", body)

    def test_module_page_with_comply_renders_verify_state(self):
        _tmp, db, _server, out = make_module("comply live mod")
        _cid, name = _concepts(db)[0]
        spec = json.dumps({"format": mod.FORMAT, "title": "Q3",
                           "required": [name, "ghost-requirement"]})
        body = handler_for(db).module_html(out["module_id"], comply_spec=spec)
        self.assertIn("id='comptrack'", body)
        self.assertIn("0 of 2 required concepts verified", body)

    def test_module_page_comply_marks_owned_verified(self):
        _tmp, db, _server, out = make_module("comply pass mod")
        from groundwork import db as dbmod
        from groundwork import ownership as ownmod
        cid, name = _concepts(db)[0]
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
        spec = json.dumps({"title": "t", "required": [name]})
        body = handler_for(db).module_html(out["module_id"], comply_spec=spec)
        self.assertIn("1 of 1 required concepts verified", body)
        self.assertIn("PASS", body)


class ComptrackShapeTest(unittest.TestCase):
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


if __name__ == "__main__":
    unittest.main()
