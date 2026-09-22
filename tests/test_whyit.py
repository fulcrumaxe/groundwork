"""Per-lesson why-this-matters from concept notes (I-109)."""
import json
import unittest

from groundwork import db as dbmod
from groundwork import whyit as whyitmod

from test_web import handler_for, make_module


class CleanNoteTest(unittest.TestCase):
    def test_blank_and_nonstring_empty(self):
        self.assertEqual(whyitmod.clean_note(""), "")
        self.assertEqual(whyitmod.clean_note("   "), "")
        self.assertEqual(whyitmod.clean_note(None), "")
        self.assertEqual(whyitmod.clean_note(123), "")

    def test_verbatim_and_capped(self):
        self.assertEqual(
            whyitmod.clean_note("  Checkout totals flow through add.  "),
            "Checkout totals flow through add.")
        self.assertLessEqual(len(whyitmod.clean_note("x" * 900)), 500)


class WhyForLessonTest(unittest.TestCase):
    def test_explicit_note_wins_verbatim(self):
        lesson = {"concept_id": "m:add", "name": "add",
                  "why_note": "Stored note."}
        self.assertEqual(whyitmod.why_for_lesson(lesson, "Agent words."),
                         "Agent words.")

    def test_stored_note_used_when_no_explicit(self):
        lesson = {"concept_id": "m:add", "name": "add",
                  "why_note": "Checkout totals flow through add."}
        self.assertIn("Checkout totals",
                      whyitmod.why_for_lesson(lesson))

    def test_absent_means_absent(self):
        self.assertEqual(whyitmod.why_for_lesson({"name": "add"}), "")
        self.assertEqual(whyitmod.why_for_lesson("nope"), "")

    def test_note_lookup_order(self):
        lesson = {"concept_id": "m:add", "name": "add"}
        notes = {"add": "By name.", "m:add": "By id."}
        self.assertEqual(whyitmod.note_for_lesson(lesson, notes), "By id.")
        self.assertEqual(whyitmod.note_for_lesson(lesson, {"add": "By name."}),
                         "By name.")
        self.assertEqual(whyitmod.note_for_lesson(lesson, {}), "")


class LessonWhyHtmlTest(unittest.TestCase):
    def test_empty_renders_empty(self):
        self.assertEqual(whyitmod.lesson_why_html({"name": "add"}), "")

    def test_note_renders_escaped_aside(self):
        out = whyitmod.lesson_why_html({"name": "add",
                                        "why_note": "Totals <b>flow</b> here."})
        self.assertIn("Why this matters", out)
        self.assertIn("Totals &lt;b&gt;flow&lt;/b&gt; here.", out)
        self.assertNotIn("<b>flow</b>", out)

    def test_first_carries_anchor(self):
        out = whyitmod.lesson_why_html({"name": "a", "why_note": "n"},
                                       first=True)
        self.assertIn("id='whyit'", out)
        out2 = whyitmod.lesson_why_html({"name": "a", "why_note": "n"})
        self.assertNotIn("id='whyit'", out2)

    def test_status_anchor_and_tour(self):
        self.assertIn(whyitmod.STATUS_ANCHOR, whyitmod.section_html())
        entry = whyitmod.tour_entry()
        self.assertEqual(
            set(entry), {"id", "kind", "title", "blurb", "path", "anchor"})


class CallerPathTest(unittest.TestCase):
    def _stamp_first_lesson(self, db, mid, note):
        con = dbmod.connect(db)
        try:
            row = con.execute("SELECT lessons FROM modules WHERE id=?",
                              (mid,)).fetchone()
            lessons = json.loads(row["lessons"])
            lessons[0]["why_note"] = note
            con.execute("UPDATE modules SET lessons=? WHERE id=?",
                        (json.dumps(lessons), mid))
            con.commit()
        finally:
            con.close()

    def test_module_page_shows_lesson_why(self):
        _tmp, db, _server, out = make_module("lesson reason mod")
        self._stamp_first_lesson(
            db, out["module_id"], "Checkout totals flow through add.")
        body = handler_for(db).module_html(out["module_id"])
        self.assertIn("Why this matters", body)
        self.assertIn("Checkout totals flow through add.", body)
        self.assertIn("id='whyit'", body)

    def test_legacy_page_has_no_why_aside(self):
        _tmp, db, _server, out = make_module("legacy reasonless mod")
        body = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("lesson-why", body)
        self.assertNotIn("id='whyit'", body)


class PipelineStampTest(unittest.TestCase):
    def test_concept_notes_stamp_why_note(self):
        from test_groundwork import agent_module_params, make_repo
        from groundwork import pipeline as pipelinemod
        repo = make_repo()
        db = str(repo / "whyit.db")
        dbmod.init_db(db)
        con = dbmod.connect(db)
        try:
            out = pipelinemod.create_module(
                con, repo=str(repo), learner_level="beginner",
                concept_notes={"add": "Checkout totals flow through add."},
                **agent_module_params("whyit stamp"))
        finally:
            con.close()
        by_name = {L["name"]: L for L in out["lessons"]}
        self.assertEqual(by_name["add"].get("why_note"),
                         "Checkout totals flow through add.")
        self.assertNotIn("why_note", by_name["greet"])


if __name__ == "__main__":
    unittest.main()
