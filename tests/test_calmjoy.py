"""Quiet celebrations: motion-free milestone and session twins (F-142)."""
import os
import tempfile
import unittest

from groundwork import emoji as emojimod
from groundwork import history as histmod
from groundwork import motion as motionmod
from groundwork import calmjoy as mod
from test_web import make_module


def _own(db):
    """Own the fixture concept with two passing ownership reviews."""
    from groundwork import db as dbmod
    from groundwork import ownership as ownmod
    con = dbmod.connect(db)
    try:
        cid = con.execute("SELECT id FROM concepts").fetchall()[0]["id"]
        card = con.execute(
            "SELECT id FROM cards WHERE concept_id=? LIMIT 1",
            (cid,)).fetchone()[0]
        con.execute("UPDATE cards SET exercise_type=? WHERE id=?",
                    (ownmod.ownership_types()[0], card))
        for _ in range(2):
            con.execute(
                "INSERT INTO reviews(card_id, grade, confidence,"
                " reviewed_at) VALUES(?, 5, 4, '2026-01-10T10:00:00Z')",
                (card,))
        con.commit()
    finally:
        con.close()


class CalmQueryTest(unittest.TestCase):
    def test_on_values(self):
        for v in ("1", "true", "yes", "on", "calm", "TRUE", " 1 "):
            self.assertTrue(mod.is_calm({"calm": [v]}), v)
        self.assertTrue(mod.is_calm("1"))

    def test_off_and_absent_fail_closed(self):
        for q in (None, {}, {"calm": []}, {"calm": ["0"]},
                  {"calm": ["false"]}, {"calm": ["no"]}, {"wager": ["x"]},
                  "0", "banana", 1, ["calm"]):
            self.assertFalse(mod.is_calm(q), repr(q))

    def test_last_value_wins(self):
        self.assertTrue(mod.is_calm({"calm": ["0", "1"]}))
        self.assertFalse(mod.is_calm({"calm": ["1", "0"]}))

    def test_toggle_carries_other_params(self):
        body = mod.toggle_html({"wager": ["probe:c:7"]})
        self.assertIn("calm=1", body)
        self.assertIn("wager=", body)
        self.assertIn("Calm view", body)
        on = mod.toggle_html({"wager": ["probe:c:7"], "calm": ["1"]})
        self.assertIn("Full view", on)
        self.assertNotIn("calm=1", on)
        self.assertIn("wager=", on)


class CalmCssTest(unittest.TestCase):
    def test_zero_motion_and_both_gates(self):
        css = mod.celebrate_css()
        self.assertNotIn("@keyframes", css)
        self.assertNotIn("animation", css)
        self.assertIn("prefers-reduced-motion", css)
        self.assertIn("force-calm", css)
        self.assertIn(".calm-joy-twin[hidden]{display:none}", css)
        css.encode("ascii")

    def test_motion_audit_passes(self):
        self.assertEqual(
            motionmod.audit_css(mod.celebrate_css()),
            {"over": [], "ungated": [], "ok": True})


class CalmLinesTest(unittest.TestCase):
    def test_milestone_escapes_and_dates(self):
        body = mod.milestone_line(
            {"label": "<b>Owned</b>", "when": "2026-09-12T10:00:00Z"})
        self.assertIn("&lt;b&gt;Owned&lt;/b&gt;", body)
        self.assertIn("2026-09-12", body)
        self.assertIn("seal", body)

    def test_milestone_hostile_is_empty(self):
        self.assertEqual(mod.milestone_line({}), "")
        self.assertEqual(mod.milestone_line(None), "")
        self.assertEqual(mod.milestone_line({"label": "  "}), "")

    def test_session_line_and_quiet(self):
        body = mod.session_line({"answered": 12, "correct": 10,
                                 "accuracy": 83, "next_due": "2026-09-28"})
        self.assertIn("[x] 12 answered today", body)
        self.assertIn("10 correct (83%)", body)
        self.assertEqual(mod.session_line({"answered": 0}), "")
        self.assertEqual(mod.session_line(None), "")
        self.assertEqual(mod.session_line({"answered": "many"}), "")

    def test_twin_absent_is_empty(self):
        self.assertEqual(mod.twin_html([], {"answered": 0}), "")
        self.assertEqual(mod.twin_html(None, None, {"calm": ["1"]}), "")

    def test_twin_calm_visible_default_hidden(self):
        ms = [{"label": "First concept owned", "when": "2026-09-12"}]
        calm = mod.twin_html(ms, {"answered": 0}, {"calm": ["1"]})
        self.assertIn("id='calm-joy'", calm)
        self.assertIn("force-calm", calm)
        self.assertNotIn("hidden", calm.split("id='calm-joy'")[1][:40])
        default = mod.twin_html(ms, {"answered": 0})
        self.assertIn("id='calm-joy' hidden", default)


class CalmCallerEffectTest(unittest.TestCase):
    def test_caller_history_calm_twin_and_legacy(self):
        _tmp, db, _server, _out = make_module("calmjoy caller mod")
        _own(db)
        calm = histmod.history_html(db, {"calm": ["1"]})
        self.assertIn("id='calm-joy'", calm)
        self.assertIn("force-calm", calm)
        self.assertIn("First concept owned", calm)
        default = histmod.history_html(db)
        self.assertIn("id='calm-joy' hidden", default)
        _tmp2, db2, _s2, _o2 = make_module("calmjoy legacy mod")
        self.assertNotIn("calm-joy", histmod.history_html(db2))
        self.assertNotIn("calm-joy",
                         histmod.history_html(db2, {"calm": ["1"]}))
        missing = os.path.join(tempfile.mkdtemp(prefix="gw-calmjoy-"),
                               "missing.db")
        self.assertEqual(mod.block_html(missing, {"calm": ["1"]}), "")


class CalmShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], mod.STATUS_ANCHOR)

    def test_status_anchor(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.status_section_html())

    def test_source_has_no_blocked_glyphs(self):
        import pathlib
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])
        src.encode("ascii")


if __name__ == "__main__":
    unittest.main()
