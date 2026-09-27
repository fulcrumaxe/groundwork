"""Flashcard flip between recall and self-rate (I-177)."""
import re
import sqlite3
import unittest

from groundwork import cards as cardsmod
from groundwork import cardflip as mod
from groundwork import emoji as emojimod
from groundwork import motion as motionmod


def _card(cid="t1", etype=1):
    return {"id": cid, "exercise_type": etype, "payload": "{}"}


def _row(cid="r1", etype=1):
    con = sqlite3.connect(":memory:")
    con.row_factory = sqlite3.Row
    con.execute("CREATE TABLE c (id TEXT, exercise_type INT)")
    con.execute("INSERT INTO c VALUES (?, ?)", (cid, etype))
    return con.execute("SELECT * FROM c").fetchone()


class CardflipUnitTest(unittest.TestCase):
    def test_is_flashcard_dict_and_row(self):
        self.assertTrue(mod.is_flashcard(_card()))
        self.assertTrue(mod.is_flashcard({"exercise_type": "1"}))
        self.assertTrue(mod.is_flashcard(_row()))

    def test_is_flashcard_rejects_hostile(self):
        self.assertFalse(mod.is_flashcard(_card(etype=5)))
        self.assertFalse(mod.is_flashcard({}))
        self.assertFalse(mod.is_flashcard(None))
        self.assertFalse(mod.is_flashcard(object()))

    def test_card_id_reads_dicts_and_rows(self):
        self.assertEqual(mod._card_id(_card("zz9")), "zz9")
        self.assertEqual(mod._card_id(_row("r2")), "r2")
        self.assertEqual(mod._card_id({}), "")
        self.assertEqual(mod._card_id(None), "")

    def test_uid_sanitized(self):
        self.assertEqual(mod._uid("a'b\"<c>"), "abc")
        self.assertEqual(mod._uid(None), "")
        self.assertEqual(mod._uid(True), "")
        self.assertEqual(mod._uid("!!!"), "")

    def test_duration_clamped_to_budget(self):
        self.assertEqual(mod.duration_ms(), 250)
        for bad in (None, "fast", True, -5, 9999, object()):
            self.assertEqual(mod.duration_ms(bad), 250)

    def test_css_raw_declarations_only(self):
        css = mod.flip_css().lower()
        self.assertNotIn("<style", css)
        self.assertIn(".cflip-inner", css)
        self.assertIn(":checked", css)
        self.assertIn("rotatey(180deg)", css.replace(" ", ""))

    def test_css_within_motion_budget_and_gated(self):
        css = mod.flip_css()
        durs = [int(m.group(1)) for m in re.finditer(r"(\d+)\s*ms", css)]
        self.assertTrue(durs)
        for ms in durs:
            self.assertLessEqual(ms, 300)
        flat = css.replace(" ", "")
        self.assertIn("prefers-reduced-motion", flat)
        self.assertIn("transition:none", flat)
        self.assertIn("transform:none", flat)
        self.assertTrue(motionmod.audit_css(css)["ok"])

    def test_css_leaves_focus_outlines_alone(self):
        css = mod.flip_css().lower()
        self.assertNotIn("outline", css)
        self.assertNotIn(":focus", css)

    def test_toggle_checkbox_posts_nothing(self):
        m = re.search(r"<input type='checkbox'[^>]*>", mod.branch_html(_card(), "t1"))
        self.assertIsNotNone(m)
        self.assertNotIn("name=", m.group(0))

    def test_ids_unique_per_card(self):
        self.assertIn("cfAAA", mod.branch_html(_card(), "AAA"))
        self.assertIn("cfBBB", mod.branch_html(_card(), "BBB"))


class CardflipEffectTest(unittest.TestCase):
    def test_caller_widget_gains_flip_with_same_fields(self):
        out = cardsmod.answer_widget(_card(), 0, "/due")
        self.assertIn("cflip-front", out)
        self.assertIn("cflip-back", out)
        self.assertIn("name='recall'", out)
        self.assertIn("name='answer'", out)
        self.assertIn("Submit rating", out)
        self.assertIn("confslider", out)
        self.assertLess(out.index("name='recall'"), out.index("name='answer'"))

    def test_caller_widget_other_types_untouched(self):
        out = cardsmod.answer_widget(_card(etype=5), 0, "/due")
        self.assertNotIn("cflip", out)

    def test_absent_id_falls_back_to_legacy_bytes(self):
        legacy = mod.legacy_body()
        for bad in ("", True, "!!!"):
            self.assertEqual(mod.branch_html(_card(), bad), legacy)
        self.assertEqual(mod.branch_html({}, None), legacy)
        self.assertIn("(optional, this is the recall)", legacy)
        self.assertIn("Then rate how well you recalled it", legacy)


class CardflipShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["id"], "flashcard-flip")
        self.assertEqual(e["kind"], "improvement")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], "status-b26-cardflip")

    def test_section_anchor_and_demo(self):
        html = mod.section_html()
        self.assertIn("id='status-b26-cardflip'", html)
        self.assertIn("cflip", html)
        self.assertIn("name='answer'", html)

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
