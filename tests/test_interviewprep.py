"""Pre-interview confidence builder: targeted recap track (F-134)."""
import copy
import unittest

from groundwork import emoji as emojimod
from groundwork import interviewprep as mod
from test_web import handler_for, make_module


def _concept(cid, mastery, name="c", mid="m1"):
    return {"id": cid, "name": f"{name}-{cid}", "module_id": mid,
            "mastery": mastery}


class InterviewprepUnitTest(unittest.TestCase):
    def test_weakest_first_stalest_breaks_ties(self):
        concepts = [_concept("a", 0.9), _concept("b", 0.2), _concept("c", 0.2)]
        due = [{"concept_id": "b", "due": "2026-09-20T00:00:00Z"},
               {"concept_id": "c", "due": "2026-09-10T00:00:00Z"}]
        picks = mod.pick_track(concepts, due)
        self.assertEqual([p["concept_id"] for p in picks], ["c", "b", "a"])

    def test_cap_and_hostile_size(self):
        concepts = [_concept(str(i), 0.1) for i in range(5)]
        self.assertEqual(len(mod.pick_track(concepts, size=2)), 2)
        self.assertEqual(len(mod.pick_track(concepts, size=99)), 5)
        self.assertEqual(len(mod.pick_track(concepts, size="junk")), 5)

    def test_dedupe_skips_non_dicts_and_freezes_input(self):
        concepts = [_concept("a", 0.1), "junk", None, _concept("a", 0.9)]
        before = copy.deepcopy(concepts)
        picks = mod.pick_track(concepts)
        self.assertEqual([p["concept_id"] for p in picks], ["a"])
        self.assertEqual(concepts, before)

    def test_empty_is_empty(self):
        self.assertEqual(mod.pick_track([]), [])
        self.assertEqual(mod.track_html([], []), "")
        self.assertEqual(mod.track_html(None, None), "")
        self.assertEqual(mod.track_html("junk"), "")

    def test_all_owned_still_renders_stalest_first(self):
        concepts = [_concept("a", 0.9), _concept("b", 0.95)]
        due = [{"concept_id": "a", "due": "2026-09-25T00:00:00Z"},
               {"concept_id": "b", "due": "2026-09-01T00:00:00Z"}]
        picks = mod.pick_track(concepts, due)
        self.assertEqual([p["concept_id"] for p in picks], ["a", "b"])

    def test_html_has_study_links_and_reasons(self):
        out = mod.track_html([_concept("a", 0.2, "loops", "m9")],
                             [{"concept_id": "a",
                               "due": "2026-09-01T00:00:00Z"}])
        self.assertIn("id='preptrack'", out)
        self.assertIn("/modules/m9#lesson-", out)
        self.assertIn("mastery 0.20", out)
        self.assertIn("Study", out)


class InterviewprepEffectTest(unittest.TestCase):
    def test_caller_due_gains_track(self):
        _tmp, db, _server, _out = make_module("prep mod")
        body = handler_for(db).due_html()
        self.assertIn("id='preptrack'", body)

    def test_empty_pool_keeps_legacy_bytes(self):
        self.assertEqual(mod.track_html([], [{"concept_id": "x"}]), "")


class InterviewprepShapeTest(unittest.TestCase):
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
