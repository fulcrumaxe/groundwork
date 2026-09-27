"""Repo tree picker for where-live cards with many files (I-180)."""
import json
import unittest

from groundwork import cards as cardsmod
from groundwork import exercises as exmod
from groundwork import treepick as tpmod


MANY = ["groundwork/cards.py", "groundwork/web.py", "groundwork/sched.py",
        "groundwork/coach.py", "groundwork/filemap.py", "tests/test_web.py",
        "docs/tour.md", "groundwork/grading.py"]
FEW = ["groundwork/cards.py", "groundwork/web.py", "groundwork/sched.py"]


def _card(**kw):
    base = {"id": "c1", "exercise_type": "4", "concept": "parse",
            "payload": json.dumps({"choices": MANY,
                                   "answer": "groundwork/cards.py",
                                   "hints": []})}
    base.update(kw)
    return base


class ThresholdTest(unittest.TestCase):
    def test_boundary_six_buttons_seven_picker(self):
        self.assertFalse(tpmod.should_pick(FEW + ["a.py", "b.py", "c.py"]))
        self.assertTrue(tpmod.should_pick(
            FEW + ["a.py", "b.py", "c.py", "d.py"]))

    def test_dedupes_before_counting(self):
        self.assertFalse(tpmod.should_pick(["a.py"] * 8))
        self.assertFalse(tpmod.should_pick(["a.py", "a.py"]))

    def test_hostile_fails_closed_to_buttons(self):
        self.assertFalse(tpmod.should_pick(None))
        self.assertFalse(tpmod.should_pick("groundwork/cards.py"))
        self.assertFalse(tpmod.should_pick({"choices": MANY}))
        self.assertFalse(tpmod.should_pick([None, 3, "  "]))


class GroupByDirTest(unittest.TestCase):
    def test_sorted_dirs_and_files(self):
        groups = tpmod.group_by_dir(
            ["b/z.py", "a/y.py", "a/x.py", "top.py"])
        self.assertEqual([d for d, _ in groups], ["", "a", "b"])
        self.assertEqual(dict(groups)["a"], ["a/x.py", "a/y.py"])
        self.assertEqual(dict(groups)[""], ["top.py"])

    def test_hostile_is_empty(self):
        self.assertEqual(tpmod.group_by_dir(None), [])
        self.assertEqual(tpmod.group_by_dir("nope"), [])
        self.assertEqual(tpmod.group_by_dir([None, 3]), [])


class LegacyHtmlTest(unittest.TestCase):
    def test_byte_exact_button_join(self):
        self.assertEqual(
            tpmod.legacy_html(["a", "b"]),
            "<button name='answer' value='a'>a</button> "
            "<button name='answer' value='b'>b</button>")

    def test_matches_cards_branch_format(self):
        row = tpmod.legacy_html(FEW)
        for c in FEW:
            self.assertIn(f"<button name='answer' value='{c}'>{c}</button>",
                          row)

    def test_hostile_is_empty(self):
        self.assertEqual(tpmod.legacy_html([]), "")
        self.assertEqual(tpmod.legacy_html(None), "")


class PickerHtmlTest(unittest.TestCase):
    def test_short_lists_and_hostile_render_nothing(self):
        self.assertEqual(tpmod.picker_html(FEW, "c1"), "")
        self.assertEqual(tpmod.picker_html([], "c1"), "")
        self.assertEqual(tpmod.picker_html(None, "c1"), "")
        self.assertEqual(tpmod.picker_html("nope", "c1"), "")

    def test_many_files_group_with_full_path_values(self):
        out = tpmod.picker_html(MANY, "c1")
        self.assertIn("id='treepick'", out)
        self.assertEqual(out.count("<details"), 3)  # groundwork+tests+docs
        self.assertIn("<details open>", out)
        for c in MANY:
            self.assertIn(f"name='answer' value='{c}'", out)
        self.assertIn("required", out)
        self.assertIn("<button>Check file</button>", out)

    def test_labels_show_basenames(self):
        out = tpmod.picker_html(MANY, "c1")
        self.assertIn("> cards.py</label>", out)
        self.assertIn("groundwork (6)", out)

    def test_escapes_hostile_paths(self):
        choices = ["<script>.py"] + [f"d/f{i}.py" for i in range(7)]
        out = tpmod.picker_html(choices, "c1")
        self.assertNotIn("<script>", out)
        self.assertIn("&lt;script&gt;.py", out)

    def test_ascii_only(self):
        tpmod.picker_html(MANY, "c1").encode("ascii")
        tpmod.section_html().encode("ascii")


class StatusAnchorAndTourTest(unittest.TestCase):
    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{tpmod.STATUS_ANCHOR}'", tpmod.section_html())
        self.assertEqual(tpmod.tour_entry(), {
            "id": "where-live-tree-picker",
            "kind": "improvement",
            "title": "Where-live tree picker",
            "blurb": ("Where-live cards with many files answer from a "
                      "directory-grouped tree picker instead of a wall "
                      "of buttons."),
            "path": "/status",
            "anchor": "status-b27-treepick",
        })


class CallerEffectTest(unittest.TestCase):
    def test_answer_widget_picker_with_grading_intact(self):
        widget = cardsmod.answer_widget(_card(), 0, "/due")
        self.assertIn("id='treepick'", widget)
        self.assertNotIn("<button name='answer'", widget)
        for c in MANY:
            self.assertIn(f"name='answer' value='{c}'", widget)
        ex = {"type": 4, "payload": {"choices": MANY,
                                    "answer": "groundwork/cards.py"}}
        self.assertTrue(exmod.grade(ex, "groundwork/cards.py")["pass"])
        self.assertFalse(exmod.grade(ex, "groundwork/web.py")["pass"])

    def test_answer_widget_few_choices_is_legacy_pinned(self):
        few = _card(payload=json.dumps({"choices": FEW,
                                        "answer": FEW[0], "hints": []}))
        widget = cardsmod.answer_widget(few, 0, "/due")
        self.assertNotIn("id='treepick'", widget)
        self.assertIn(tpmod.legacy_html(FEW), widget)
        self.assertEqual(
            tpmod.branch_html(few, {"choices": FEW}, "c1"),
            f"{tpmod.legacy_html(FEW)} {cardsmod._confidence()}")

    def test_answer_widget_hostile_payload_renders(self):
        bare = _card(payload=json.dumps({"hints": []}))
        widget = cardsmod.answer_widget(bare, 0, "/due")
        self.assertNotIn("id='treepick'", widget)
        self.assertIn("name='origin'", widget)


if __name__ == "__main__":
    unittest.main()
