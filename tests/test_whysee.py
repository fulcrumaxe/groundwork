"""Shared Why am I seeing this reasons for recommendations (F-138)."""
import unittest

from groundwork import blindspots as blindmod
from groundwork import emoji as emojimod
from groundwork import interviewprep as prepmod
from groundwork import lessons as lesmod
from groundwork import partytrick as partymod
from groundwork import related as relmod
from groundwork import reteach as reteachmod
from groundwork import serendipity as sermod
from groundwork import whysee as mod

from test_web import agent_params, make_module


def _lesson(**kw):
    base = {"concept_id": "c", "name": "add", "kind": "function",
            "file": "calc.py", "line": 1, "summary": "Adds a and b.",
            "docstring": "", "callers": [], "callees": [],
            "key_lines": "", "source": "def add(a, b):\n    return a + b\n",
            "how": ["take a", "take b", "return total"], "worked": None,
            "dualcode": {"steps": ["take a", "take b", "return total"],
                         "states": []}}
    base.update(kw)
    return base


OWNED = [{"name": "total", "summary": "running sum accumulator"},
         {"name": "main", "summary": "entry point calling add"}]


class ReasonForTest(unittest.TestCase):
    def test_preptrack_ascii_mastery_and_due(self):
        self.assertEqual(
            mod.reason_for("preptrack", {"mastery": 0.2,
                                        "due": "2026-09-01T00:00:00Z"}),
            "mastery 0.20; due 2026-09-01")
        self.assertEqual(mod.reason_for("preptrack", {}), "mastery 0.00")

    def test_blindspot_rank_and_pct(self):
        self.assertEqual(
            mod.reason_for("blindspot", {"mastery": 0.12, "limit": 10}),
            "mastery 12%; among your 10 lowest-mastery concepts")
        self.assertEqual(mod.reason_for("blindspot", {}), "")

    def test_serendipity_module_and_queue(self):
        self.assertEqual(
            mod.reason_for("serendipity", {"module": "loops",
                                          "in_due": False}),
            "in loops; not in your due queue")
        self.assertEqual(mod.reason_for("serendipity", {}), "")

    def test_elaboration_and_related(self):
        self.assertEqual(
            mod.reason_for("elaboration", {"shared": ["a", "b"],
                                          "same_repo": True,
                                          "owned": True}),
            "shares: a, b; same repo; you own it")
        self.assertEqual(
            mod.reason_for("related", {"same_repo": True,
                                      "shared": ["add"]}),
            "same repo; shares: add")

    def test_reteach_and_partytrick(self):
        self.assertEqual(
            mod.reason_for("reteach", {"first_seen": "2026-08-01T00:00:00Z",
                                      "days_ago": 45}),
            "first tried 2026-08-01; 45 days ago")
        self.assertEqual(mod.reason_for("partytrick", {"owned_count": 7}),
                         "1 of 7 concepts you own")
        self.assertEqual(mod.reason_for("partytrick", {}), "")

    def test_unknown_source_and_hostile_facts(self):
        self.assertEqual(mod.reason_for("nope", {"mastery": 1}), "")
        self.assertEqual(mod.reason_for(None, None), "")
        for bad in (None, "junk", [], 42):
            self.assertEqual(mod.reason_for("preptrack", bad),
                             "mastery 0.00")
            self.assertEqual(mod.reason_for("blindspot", bad), "")
        self.assertEqual(
            mod.reason_for("blindspot", {"mastery": float("nan")}), "")


class ReasonHtmlTest(unittest.TestCase):
    def test_note_marks_first_only(self):
        out = mod.reason_html("mastery 0.20", first=True)
        self.assertIn("id='whysee'", out)
        self.assertIn("Why am I seeing this?", out)
        self.assertIn("mastery 0.20", out)
        self.assertNotIn("id='whysee'", mod.reason_html("mastery 0.20"))

    def test_empty_and_hostile_render_nothing(self):
        for bad in ("", "   ", None, 0, [], {}):
            self.assertEqual(mod.reason_html(bad), "")

    def test_escapes_reason_text(self):
        out = mod.reason_html("<b>loops</b>")
        self.assertIn("&lt;b&gt;loops&lt;/b&gt;", out)
        self.assertNotIn("<b>loops</b>", out)


class ElaborationHtmlTest(unittest.TestCase):
    def test_partners_gain_live_notes(self):
        out = mod.elaboration_html(_lesson(), OWNED, ["main", "total"])
        self.assertIn("Why am I seeing this?", out)
        self.assertIn("shares: add", out)
        self.assertIn("you own it", out)
        self.assertIn("main:", out)

    def test_first_flag_marks_first_note(self):
        out = mod.elaboration_html(_lesson(), OWNED, ["main", "total"],
                                   first=True)
        self.assertEqual(out.count("id='whysee'"), 1)

    def test_unknown_partners_and_hostile_render_nothing(self):
        self.assertEqual(
            mod.elaboration_html(_lesson(), OWNED, ["ghost"]), "")
        self.assertEqual(mod.elaboration_html(_lesson(), OWNED, []), "")
        self.assertEqual(mod.elaboration_html(None, None, None), "")
        self.assertEqual(mod.elaboration_html("junk", "junk", "junk"), "")


class CallerEffectTest(unittest.TestCase):
    def test_lesson_rendering_gains_why_note(self):
        out = lesmod.render_levels(_lesson(), 0.9, 9, "auto", "/",
                                   owned=OWNED)
        self.assertIn("elaboration drill", out)
        self.assertIn("Why am I seeing this?", out)
        self.assertIn("shares: add", out)

    def test_absent_data_keeps_legacy_bytes(self):
        for owned in (None, [], [{"name": "solo", "summary": "only one"}]):
            out = lesmod.render_levels(_lesson(), 0.9, 9, "auto", "/",
                                       owned=owned)
            self.assertNotIn("whysee", out)
            self.assertNotIn("Why am I seeing this?", out)


class SurfacesEffectTest(unittest.TestCase):
    """Every wired surface renders its live reason; empties stay legacy."""

    def test_serendipity_bonus_cites_module_and_queue(self):
        _tmp, db, _server, _out = make_module("whysee ser mod")
        from groundwork import db as dbmod
        con = dbmod.connect(db)
        try:
            cid = con.execute("SELECT id FROM concepts LIMIT 1").fetchone()[0]
            con.execute("UPDATE cards SET due='2999-01-01T00:00:00Z'"
                        " WHERE concept_id=?", (cid,))
            con.commit()
        finally:
            con.close()
        cand = sermod.pick(db)
        out = sermod.section_html(db)
        if cand is None:
            self.assertIn("whole neighborhood", out)
            self.assertNotIn("Why am I seeing this?", out)
        else:
            self.assertIn("Why am I seeing this?", out)
            self.assertIn("not in your due queue", out)

    def test_serendipity_empty_db_is_legacy(self):
        import os
        import tempfile
        from groundwork import db as dbmod
        p = tempfile.mktemp(suffix=".db")
        dbmod.init_db(p)
        try:
            out = sermod.section_html(p)
        finally:
            os.unlink(p)
        self.assertIn("whole neighborhood", out)
        self.assertNotIn("Why am I seeing this?", out)

    def test_preptrack_rows_cite_mastery_and_due(self):
        concepts = [{"id": "a", "name": "c-a", "module_id": "m1",
                     "mastery": 0.2}]
        due = [{"concept_id": "a", "due": "2026-09-01T00:00:00Z"}]
        out = prepmod.track_html(concepts, due)
        self.assertIn("Why am I seeing this?", out)
        self.assertIn("mastery 0.20; due 2026-09-01", out)
        self.assertIn("mastery 0.20", out)  # existing reason untouched
        self.assertEqual(prepmod.track_html([], []), "")

    def test_blindspot_rows_cite_mastery_rank(self):
        _tmp, db, _server, _out = make_module("whysee blind mod")
        out = blindmod.section_html(db)
        self.assertIn("Why am I seeing this?", out)
        self.assertIn("among your 10 lowest-mastery concepts", out)

    def test_related_items_cite_repo_and_shared_names(self):
        tmp, db, server, out = make_module("whysee rel one")
        from groundwork import tour as tourmod
        mid, _ = tourmod.targets(db)
        params = {"repo_path": str(tmp)}
        params.update(agent_params("whysee rel two"))
        created = server.tool_create_learning_module(params)
        assert "module_id" in created, created.get("error")
        out = relmod.related_html(db, mid)
        self.assertIn("Why am I seeing this?", out)
        self.assertIn("same repo", out)

    def test_partytrick_cites_owned_count(self):
        _tmp, db, _server, _out = make_module("whysee party mod")
        from groundwork import db as dbmod
        from groundwork import ownership as ownmod
        etype = ownmod.ownership_types()[0]
        con = dbmod.connect(db)
        try:
            cid = con.execute("SELECT id FROM concepts").fetchall()[0]["id"]
            card = con.execute(
                "SELECT id FROM cards WHERE concept_id=? LIMIT 1",
                (cid,)).fetchone()[0]
            con.execute("UPDATE cards SET exercise_type=? WHERE id=?",
                        (etype, card))
            for _ in range(2):
                con.execute(
                    "INSERT INTO reviews(card_id, grade, confidence,"
                    " reviewed_at) VALUES(?, 5, 4, '2026-09-20T10:00:00Z')",
                    (card,))
            con.commit()
        finally:
            con.close()
        out = partymod.section_html(db, seed=1)
        self.assertIn("Why am I seeing this?", out)
        self.assertIn("concepts you own", out)

    def test_partytrick_locked_is_legacy(self):
        _tmp, db, _s, _out = make_module("whysee party locked")
        out = partymod.section_html(db, seed=1)
        self.assertIn("No party tricks yet", out)
        self.assertNotIn("Why am I seeing this?", out)

    def test_reteach_blocks_cite_first_seen(self):
        out = reteachmod.reteach_box_html([{
            "name": "add", "first_seen": "2026-08-01T00:00:00Z",
            "recording": "totals two numbers"}])
        self.assertIn("Why am I seeing this?", out)
        self.assertIn("first tried 2026-08-01", out)
        self.assertEqual(reteachmod.reteach_box_html([]), "")
        bare = reteachmod.reteach_box_html([{"name": "add"}])
        self.assertNotIn("Why am I seeing this?", bare)


class WhyseeShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["anchor"], mod.STATUS_ANCHOR)

    def test_section_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", mod.section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertTrue(src.isascii())
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
