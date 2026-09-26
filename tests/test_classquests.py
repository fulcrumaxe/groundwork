"""Classroom quests: teacher-defined checklists, completion-based (F-130)."""
import json
import unittest

from groundwork import classquests as mod
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


class ClassquestsUnitTest(unittest.TestCase):
    def test_parse_spec_dict_and_json(self):
        spec = {"format": mod.FORMAT, "title": "W3", "steps": ["a", "b"]}
        self.assertEqual(mod.parse_spec(spec)["steps"], ["a", "b"])
        self.assertEqual(mod.parse_spec(json.dumps(spec))["title"], "W3")

    def test_parse_spec_drops_blanks_and_dupes(self):
        p = mod.parse_spec({"title": "t", "steps": ["a", "", "a", " b "]})
        self.assertEqual(p["steps"], ["a", "b"])

    def test_parse_spec_garbage_is_empty(self):
        self.assertEqual(mod.parse_spec("{bad"), {"title": "", "steps": []})
        self.assertEqual(mod.parse_spec(None), {"title": "", "steps": []})
        self.assertEqual(mod.parse_spec(42), {"title": "", "steps": []})

    def test_quest_view_completion(self):
        v = mod.quest_view({"title": "t", "steps": ["a", "b"]}, owned={"a"})
        self.assertEqual((v["done"], v["total"]), (1, 2))
        self.assertEqual(v["next"], "b")
        self.assertFalse(v["complete"])

    def test_quest_view_mastery_counts_at_threshold(self):
        v = mod.quest_view({"steps": ["a"]}, mastery_of={"a": 0.9})
        self.assertTrue(v["complete"])
        v = mod.quest_view({"steps": ["a"]}, mastery_of={"a": 0.5})
        self.assertFalse(v["complete"])

    def test_quest_view_hostile(self):
        v = mod.quest_view(None, owned=None, mastery_of="junk")
        self.assertEqual((v["total"], v["next"]), (0, None))

    def test_quest_html_renders_and_escapes(self):
        out = mod.quest_html({"title": "t", "steps": ["a<script>", "b"]},
                             owned={"a<script>"})
        self.assertIn("id='classquests'", out)
        self.assertIn("quest-done", out)
        self.assertIn("quest-todo", out)
        self.assertNotIn("<script>", out)
        self.assertNotIn("leaderboard", out.casefold())

    def test_quest_html_empty_without_spec(self):
        self.assertEqual(mod.quest_html(None), "")
        self.assertEqual(mod.quest_html({}), "")
        self.assertEqual(mod.quest_html("not json"), "")


class ClassquestsEffectTest(unittest.TestCase):
    def test_module_page_without_quest_is_legacy(self):
        _tmp, db, _server, out = make_module("quest legacy mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("id='classquests'", body)

    def test_module_page_with_quest_renders_checklist(self):
        _tmp, db, _server, out = make_module("quest live mod")
        _cid, name = _concepts(db)[0]
        spec = json.dumps({"format": mod.FORMAT, "title": "Week 1",
                           "steps": [name, "ghost-step"]})
        body = handler_for(db).module_html(out["module_id"], quest_spec=spec)
        self.assertIn("id='classquests'", body)
        self.assertIn("0 of 2 steps complete", body)

    def test_module_page_quest_marks_owned_done(self):
        _tmp, db, _server, out = make_module("quest done mod")
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
        spec = json.dumps({"title": "t", "steps": [name]})
        body = handler_for(db).module_html(out["module_id"], quest_spec=spec)
        self.assertIn("1 of 1 steps complete", body)
        self.assertIn("quest complete", body)


class ClassquestsShapeTest(unittest.TestCase):
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
