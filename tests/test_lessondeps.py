"""Lesson dependency jump links (I-131)."""
import json
import unittest

from groundwork import db as dbmod
from groundwork import lessondeps as ldmod
from groundwork import lessons as lesmod

from test_web import handler_for, make_module


class NeedsOfTest(unittest.TestCase):
    def test_reads_needs_and_depends_on(self):
        self.assertEqual(ldmod.needs_of({"needs": ["a", "b"]}), ["a", "b"])
        self.assertEqual(ldmod.needs_of({"depends_on": "a"}), ["a"])
        self.assertEqual(
            ldmod.needs_of({"needs": ["a", "a", " ", 7, None]}), ["a"])

    def test_missing_or_hostile_is_empty(self):
        self.assertEqual(ldmod.needs_of({}), [])
        self.assertEqual(ldmod.needs_of(None), [])
        self.assertEqual(ldmod.needs_of("nope"), [])
        self.assertEqual(ldmod.needs_of({"needs": 42}), [])


class DepsForTest(unittest.TestCase):
    def test_matches_earlier_in_order(self):
        lesson = {"name": "c", "needs": ["b", "a"]}
        earlier = [{"name": "a"}, {"name": "b"}]
        self.assertEqual(ldmod.deps_for(lesson, earlier), ["a", "b"])

    def test_slug_matching_unmatched_dropped_and_no_self_link(self):
        lesson = {"name": "For Loops", "needs": ["for loops", "charts"]}
        earlier = [{"name": "for loops"}]
        self.assertEqual(ldmod.deps_for(lesson, earlier), ["for loops"])
        self.assertEqual(ldmod.deps_for({"name": "a", "needs": ["a"]},
                                        [{"name": "a"}]), [])

    def test_no_needs_is_empty_and_hostile_never_raises(self):
        self.assertEqual(ldmod.deps_for({"name": "a"}, [{"name": "b"}]), [])
        self.assertEqual(ldmod.deps_for(None, None), [])
        self.assertEqual(ldmod.deps_for("nope", 42), [])


class DepsHtmlTest(unittest.TestCase):
    def test_jump_links_match_section_anchors(self):
        earlier = [{"name": "For Loops"}]
        body = ldmod.deps_html({"name": "c", "needs": ["For Loops"]},
                               earlier)
        anchor = "lesson-" + lesmod.slug("For Loops")
        self.assertIn("Understand first", body)
        self.assertIn(f"#{anchor}", body)
        self.assertIn("For Loops", body)

    def test_empty_renders_empty(self):
        self.assertEqual(ldmod.deps_html({"name": "a"}, [{"name": "b"}]), "")
        self.assertEqual(ldmod.deps_html(None, None), "")

    def test_names_are_escaped(self):
        body = ldmod.deps_html({"name": "c", "needs": ["<b>"]},
                               [{"name": "<b>"}])
        self.assertNotIn("<b>", body.replace("class='deps'", ""))


def _add_second_concept(db, mid):
    """Second lesson needing the first; returns nothing."""
    con = dbmod.connect(db)
    try:
        first = con.execute(
            "SELECT id, kind, file, line, mastery FROM concepts"
            " WHERE module_id=? ORDER BY rowid LIMIT 1",
            (mid,)).fetchone()
        second_id = f"{mid}:calc.py:total"
        con.execute(
            "INSERT INTO concepts (id, module_id, name, kind, file,"
            " line, mastery) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (second_id, mid, "total", first["kind"], first["file"],
             first["line"], 0.0))
        row = con.execute("SELECT lessons FROM modules WHERE id=?",
                          (mid,)).fetchone()[0]
        lessons = json.loads(row or "[]")
        second = dict(lessons[0])
        second.update({"concept_id": "calc.py:total", "name": "total",
                       "needs": ["add"]})
        lessons.append(second)
        con.execute("UPDATE modules SET lessons=? WHERE id=?",
                    (json.dumps(lessons), mid))
        con.commit()
    finally:
        con.close()


class CallerEffectTest(unittest.TestCase):
    def test_module_html_lists_earlier_lesson_first(self):
        tmp, db, server, out = make_module("lessondeps chain mod")
        mid = out["module_id"]
        _add_second_concept(db, mid)
        body = handler_for(db).module_html(mid)
        self.assertIn("Understand first", body)
        self.assertIn("#lesson-add", body)
        # Exactly one lesson carries needs: the first stays clean.
        self.assertEqual(body.count("Understand first"), 1)

    def test_module_html_legacy_without_needs(self):
        tmp, db, server, out = make_module("lessondeps legacy mod")
        base = handler_for(db).module_html(out["module_id"])
        self.assertNotIn("Understand first", base)

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{ldmod.STATUS_ANCHOR}'",
                      ldmod.section_html())
        e = ldmod.tour_entry()
        self.assertEqual(e, {
            "id": "lesson-dependencies",
            "kind": "improvement",
            "title": "Lesson dependencies",
            "blurb": ("Each lesson lists what to understand first, with "
                      "jump links back to the earlier lesson sections."),
            "path": "/status",
            "anchor": "status-b21-lessondeps",
        })


if __name__ == "__main__":
    unittest.main()
