"""Self-assigned study plans from owned proofs (F-164)."""
import json
import unittest

from groundwork import db as dbmod
from groundwork import emoji as emojimod
from groundwork import ownership as ownmod
from groundwork import selfassign as mod

from test_web import handler_for, make_module


def _names(db):
    con = dbmod.connect(db)
    try:
        return [r["name"] for r in
                con.execute("SELECT name FROM concepts").fetchall()]
    finally:
        con.close()


def _earn_owned(db):
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
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


class ParseTest(unittest.TestCase):
    def test_dict_and_json(self):
        spec = {"format": "groundwork-assign/1", "title": "T",
                "repo": "r", "due": "2026-10-01", "steps": ["a", "b"]}
        self.assertEqual(mod.parse_spec(spec)["steps"], ["a", "b"])
        self.assertEqual(mod.parse_spec(json.dumps(spec))["title"], "T")

    def test_blanks_dupes_dropped_bad_due_cleared(self):
        spec = mod.parse_spec({"steps": ["a", "", "a", " b "],
                               "due": "2026-02-30"})
        self.assertEqual(spec["steps"], ["a", "b"])
        self.assertEqual(spec["due"], "")

    def test_garbage_is_empty(self):
        for bad in (None, 5, "not-json{", [1], {"format": "other/9"}):
            self.assertEqual(mod.parse_spec(bad)["steps"], [])


class DaysLeftTest(unittest.TestCase):
    def test_inclusive_count(self):
        self.assertEqual(mod.days_left("2026-09-27", "2026-09-27"), 1)
        self.assertEqual(mod.days_left("2026-09-28", "2026-09-27"), 2)

    def test_unknown_and_overdue(self):
        self.assertIsNone(mod.days_left("", "2026-09-27"))
        self.assertIsNone(mod.days_left(None, "2026-09-27"))
        self.assertEqual(mod.days_left("2026-09-25", "2026-09-27"), -2)


class PlanViewTest(unittest.TestCase):
    def test_completion_next_pace(self):
        v = mod.plan_view({"steps": ["a", "b", "c"], "due": "2026-10-01"},
                          ["a"], {}, "", "2026-09-27")
        self.assertEqual((v["done"], v["total"]), (1, 3))
        self.assertEqual(v["next"], "b")
        self.assertFalse(v["complete"])
        # 2 remaining over 5 inclusive days -> 1 per day.
        self.assertEqual(v["pace"], 1)

    def test_mastery_counts_and_undated_pace_none(self):
        v = mod.plan_view({"steps": ["a", "b"]}, [], {"a": 0.9})
        self.assertEqual(v["done"], 1)
        self.assertIsNone(v["pace"])

    def test_scope_ok(self):
        v = mod.plan_view({"steps": ["a"], "repo": "r"}, [], {}, "r")
        self.assertTrue(v["scope_ok"])
        v = mod.plan_view({"steps": ["a"], "repo": "r"}, [], {}, "other")
        self.assertFalse(v["scope_ok"])
        v = mod.plan_view({"steps": ["a"]}, [], {}, "r")
        self.assertTrue(v["scope_ok"])


class HtmlTest(unittest.TestCase):
    def test_plan_escapes_and_empty_without_steps(self):
        out = mod.plan_html({"steps": ["<b>"]})
        self.assertIn("&lt;b&gt;", out)
        self.assertNotIn("<b>", out.replace("&lt;b&gt;", ""))
        self.assertEqual(mod.plan_html({"steps": []}), "")
        self.assertEqual(mod.plan_html(None), "")

    def test_builder_bounded_to_names(self):
        out = mod.builder_html(["a", "b"], "r", "m1")
        self.assertIn("name='astep' value='a'", out)
        self.assertIn("name='assign' value='new'", out)
        self.assertEqual(mod.builder_html([]), "")


class CallerEffectTest(unittest.TestCase):
    def test_legacy_module_page_has_no_plan(self):
        tmp, db, server, out = make_module("selfassign legacy mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("id='selfassign'", body)

    def test_spec_renders_plan_with_countdown(self):
        tmp, db, server, out = make_module("selfassign spec mod")
        name = _names(db)[0]
        spec = json.dumps({"format": "groundwork-assign/1",
                           "title": "Week plan", "repo": "",
                           "due": "2999-01-05", "steps": [name]})
        body = handler_for(db).module_html(out["module_id"],
                                           assign_spec=spec)
        self.assertIn("id='selfassign'", body)
        self.assertIn("0 of 1", body)
        self.assertIn("days left", body)

    def test_owned_proof_completes_plan(self):
        tmp, db, server, out = make_module("selfassign owned mod")
        name = _names(db)[0]
        _earn_owned(db)
        spec = json.dumps({"steps": [name]})
        body = handler_for(db).module_html(out["module_id"],
                                           assign_spec=spec)
        self.assertIn("1 of 1", body)
        self.assertIn("complete", body)

    def test_builder_and_fields_round_trip(self):
        tmp, db, server, out = make_module("selfassign build mod")
        name = _names(db)[0]
        body = handler_for(db).module_html(out["module_id"],
                                           assign_spec="new")
        self.assertIn("New study plan", body)
        self.assertIn(f"value='{name}'", body)
        fields = {"title": "T", "due": "", "steps": [name], "repo": ""}
        body = handler_for(db).module_html(out["module_id"],
                                           assign_spec="new",
                                           assign_fields=fields)
        self.assertIn("id='selfassign'", body)
        self.assertIn("?assign=", body)

    def test_garbage_spec_is_legacy(self):
        tmp, db, server, out = make_module("selfassign garbage mod")
        body = handler_for(db).module_html(out["module_id"],
                                           assign_spec="[[[")
        self.assertNotIn("id='selfassign'", body)


class ShapeTest(unittest.TestCase):
    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual((e["id"], e["kind"], e["path"], e["anchor"]),
                         ("selfassign-plan", "feature",
                          "/status", mod.STATUS_ANCHOR))

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
