"""Learning-style tuning (F-98): mix from performance, not quiz."""
import json
import unittest

from groundwork import db as dbmod
from groundwork import stylemix as smod

from test_web import handler_for, make_module


def _recs(kind, passes, total, grade_pass=5, grade_fail=2):
    recs = []
    for i in range(total):
        grade = grade_pass if i < passes else grade_fail
        recs.append((kind, grade))
    return recs


class ClassifyCardTest(unittest.TestCase):
    def test_visual_lesson_classifies_visual(self):
        card = {"summary": "short",
                "dualcode": {"steps": ["draw the loop"]}}
        self.assertEqual(smod.classify_card(card), "visual")

    def test_text_lesson_classifies_textual(self):
        card = {"summary": " ".join(["word"] * 60)}
        self.assertEqual(smod.classify_card(card), "textual")

    def test_hostile_input_is_mixed(self):
        self.assertEqual(smod.classify_card(None), "mixed")
        self.assertEqual(smod.classify_card("nope"), "mixed")
        self.assertEqual(smod.classify_card({}), "mixed")


class AffinityTest(unittest.TestCase):
    def test_no_data_falls_back_to_even(self):
        self.assertEqual(smod.affinity([]), 0.0)
        self.assertEqual(smod.affinity(None), 0.0)

    def test_too_few_attempts_falls_back_to_even(self):
        recs = [("visual", 5)] + [("textual", 2)]
        self.assertEqual(smod.affinity(recs), 0.0)

    def test_visual_strength_goes_positive(self):
        recs = (_recs("visual", 3, 3) + _recs("textual", 0, 3))
        self.assertGreater(smod.affinity(recs), 0.0)

    def test_textual_strength_goes_negative(self):
        recs = (_recs("visual", 0, 3) + _recs("textual", 3, 3))
        self.assertLess(smod.affinity(recs), 0.0)

    def test_equal_rates_go_neutral(self):
        recs = (_recs("visual", 2, 3) + _recs("textual", 2, 3))
        self.assertEqual(smod.affinity(recs), 0.0)

    def test_mixed_and_garbage_ignored(self):
        recs = (_recs("visual", 3, 3) + _recs("textual", 0, 3)
                + [("mixed", 5), ("visual", "error"), ("textual", None)])
        self.assertGreater(smod.affinity(recs), 0.0)


class RecordsForTest(unittest.TestCase):
    def _page(self):
        visual = {"summary": "short",
                  "dualcode": {"steps": ["draw it"]}}
        textual = {"summary": " ".join(["w"] * 60)}
        history = {"c1": [{"grade": 5}, {"grade": 4}],
                   "c2": [{"grade": 1}]}
        cards = {"m:calc.py:add": [{"id": "c1"}],
                 "m:calc.py:total": [{"id": "c2"}]}
        lessons = {"calc.py:add": visual, "calc.py:total": textual}
        return history, cards, lessons

    def test_pairs_grades_with_lesson_kind(self):
        history, cards, lessons = self._page()
        recs = smod.records_for(history, cards, lessons)
        self.assertEqual(recs, [("visual", 5), ("visual", 4),
                               ("textual", 1)])

    def test_mixed_lessons_and_hostile_skipped(self):
        recs = smod.records_for({"c1": [{"grade": 5}, {"nope": 1}]},
                                {"m:add": [{"id": "c1"}]},
                                {"calc.py:add": {"summary": "x"}})
        self.assertEqual(recs, [])
        self.assertEqual(smod.records_for(None, None, None), [])
        self.assertEqual(smod.records_for("x", "y", "z"), [])

    def test_db_row_shapes_without_dot_get(self):
        # Queue card rows are sqlite3.Row (no .get): the caller path
        # must still extract grades.
        class Row:
            def __init__(self, mapping):
                self._m = mapping

            def __getitem__(self, key):
                return self._m[key]

        visual = {"summary": "short",
                  "dualcode": {"steps": ["draw it"]}}
        recs = smod.records_for(
            {"c1": [Row({"grade": 5})]},
            {"m:calc.py:add": [Row({"id": "c1"})]},
            {"calc.py:add": visual})
        self.assertEqual(recs, [("visual", 5)])


class MixForTest(unittest.TestCase):
    def test_even_mix_at_zero(self):
        self.assertEqual(smod.mix_for(0.0),
                         {"visual": 50, "textual": 50})

    def test_shares_sum_to_100_and_clamp(self):
        for value in (-2.0, -1.0, -0.4, 0.4, 1.0, 2.0, "junk", None):
            mix = smod.mix_for(value)
            self.assertEqual(mix["visual"] + mix["textual"], 100)
        self.assertEqual(smod.mix_for(1.0)["visual"], 75)
        self.assertEqual(smod.mix_for(-1.0)["textual"], 75)


class OrderSectionsTest(unittest.TestCase):
    def test_legacy_no_data_keeps_text_first(self):
        lesson = {"summary": "x",
                  "dualcode": {"steps": ["draw it"]}}
        self.assertEqual(smod.order_sections(lesson, 0.0)[0], "text")
        self.assertEqual(smod.order_sections(lesson)[0], "text")

    def test_visual_affinity_puts_visual_first(self):
        lesson = {"summary": "x",
                  "dualcode": {"steps": ["draw it"]}}
        self.assertEqual(smod.order_sections(lesson, 0.6)[0], "visual")

    def test_text_only_lesson_stays_text_first(self):
        lesson = {"summary": " ".join(["w"] * 60)}
        self.assertEqual(smod.order_sections(lesson, 0.9)[0], "text")


def _add_textual_concept(db, mid):
    """Second concept with a long text-only lesson; returns its card id."""
    con = dbmod.connect(db)
    try:
        first = con.execute(
            "SELECT kind, file, line FROM concepts"
            " WHERE module_id=? ORDER BY rowid LIMIT 1",
            (mid,)).fetchone()
        con.execute(
            "INSERT INTO concepts (id, module_id, name, kind, file,"
            " line, mastery) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (f"{mid}:calc.py:total", mid, "total", first["kind"],
             first["file"], first["line"], 0.0))
        row = con.execute("SELECT lessons FROM modules WHERE id=?",
                          (mid,)).fetchone()[0]
        lessons = json.loads(row or "[]")
        second = dict(lessons[0])
        second.update({"concept_id": "calc.py:total", "name": "total",
                       "summary": " ".join(["word"] * 60),
                       "dualcode": {}, "worked": {}, "figure": None,
                       "callers": [], "callees": []})
        lessons.append(second)
        con.execute("UPDATE modules SET lessons=? WHERE id=?",
                    (json.dumps(lessons), mid))
        card_id = f"{mid}:total-ex001"
        con.execute(
            "INSERT INTO cards (id, concept_id, exercise_type, front)"
            " VALUES (?, ?, ?, ?)",
            (card_id, f"{mid}:calc.py:total", "1", "What is total?"))
        con.commit()
        return card_id
    finally:
        con.close()


def _make_visual(db, mid):
    """Fixture lesson becomes visual: call graph plus sparse text."""
    con = dbmod.connect(db)
    try:
        row = con.execute("SELECT lessons FROM modules WHERE id=?",
                          (mid,)).fetchone()[0]
        lessons = json.loads(row or "[]")
        lessons[0]["callers"] = ["helper"]
        lessons[0]["callees"] = ["total"]
        lessons[0]["summary"] = "Adds two numbers."
        lessons[0]["how"] = ["Trace the total."]
        lessons[0]["docstring"] = ""
        lessons[0]["key_lines"] = []
        con.execute("UPDATE modules SET lessons=? WHERE id=?",
                    (json.dumps(lessons), mid))
        con.commit()
    finally:
        con.close()


class CallerEffectTest(unittest.TestCase):
    """Lesson path orders visual blocks by measured affinity."""

    def test_visual_affinity_leads_with_diagram(self):
        tmp, db, server, out = make_module("stylemix visual mod")
        mid = out["module_id"]
        other = _add_textual_concept(db, mid)
        _make_visual(db, mid)
        mine = [c["id"] for c in server.tool_list_due_reviews(
            {"limit": 20})["due"]
            if c["concept_id"].endswith(":calc.py:add")
            and str(c.get("exercise_type")) == "1"][0]
        for _ in range(3):
            server.submit_review(mine, "5", 4)
            server.submit_review(other, "0", 3)
        body = handler_for(db).module_html(mid)
        self.assertIn("<svg class='callgraph'", body)
        self.assertLess(body.index("<svg class='callgraph'"),
                        body.index("Recall first"))

    def test_legacy_no_data_keeps_text_first(self):
        tmp, db, server, out = make_module("stylemix legacy mod")
        mid = out["module_id"]
        _add_textual_concept(db, mid)
        _make_visual(db, mid)
        body = handler_for(db).module_html(mid)
        self.assertIn("<svg class='callgraph'", body)
        self.assertLess(body.index("Recall first"),
                        body.index("<svg class='callgraph'"))

    def test_section_html_and_tour(self):
        self.assertIn("id='status-b21-stylemix'", smod.section_html())
        e = smod.tour_entry()
        self.assertEqual(e, {
            "id": "stylemix-tuning",
            "kind": "feature",
            "title": "Learning-style tuning",
            "blurb": "Visual-vs-textual mix follows performance, not a quiz.",
            "path": "/status",
            "anchor": "status-b21-stylemix",
        })


if __name__ == "__main__":
    unittest.main()
