"""Culturally neutral milestone copy selected by ?tone=plain (F-143)."""
import unittest

from groundwork import emoji as emojimod
from groundwork import history as histmod
from groundwork import plaincopy as mod
from test_web import make_module


def _own_one(db):
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
                " reviewed_at) VALUES(?, 5, 4, '2026-09-10T10:00:00Z')",
                (card,))
        con.commit()
    finally:
        con.close()


class PlaincopyUnitTest(unittest.TestCase):
    def test_tone_from_query_shapes(self):
        self.assertEqual(mod.tone_from_query(None), "default")
        self.assertEqual(mod.tone_from_query({}), "default")
        self.assertEqual(mod.tone_from_query({"tone": ["plain"]}), "plain")
        self.assertEqual(mod.tone_from_query({"tone": "plain"}), "plain")
        self.assertEqual(mod.tone_from_query({"tone": [" Plain "]}), "plain")
        self.assertEqual(mod.tone_from_query({"tone": [""]}), "default")
        self.assertEqual(mod.tone_from_query({"tone": []}), "default")
        self.assertEqual(mod.tone_from_query({"tone": ["verbose"]}),
                         "default")
        self.assertEqual(mod.tone_from_query({"wager": ["acc:80"]}),
                         "default")
        self.assertEqual(mod.tone_from_query("plain"), "default")
        self.assertEqual(mod.tone_from_query(42), "default")

    def test_apply_identity_by_default(self):
        sample = "<h2 id='milestones'>Milestone moments</h2> Owntober!"
        self.assertIs(mod.apply(sample), sample)
        self.assertIs(mod.apply(sample, "default"), sample)
        self.assertIs(mod.apply(sample, "verbose"), sample)
        self.assertIs(mod.apply(sample, None), sample)

    def test_apply_swaps_every_pair(self):
        self.assertEqual(len(mod.pairs()), 8)
        for old, new in mod.pairs():
            self.assertEqual(mod.apply(f"<p>{old}</p>", "plain"),
                             f"<p>{new}</p>")
        combo = "Milestone moments Owntober Nicely done."
        self.assertEqual(mod.apply(combo, "plain"),
                         "Milestones October goal Goal complete.")

    def test_apply_hostile(self):
        self.assertIsNone(mod.apply(None, "plain"))
        self.assertEqual(mod.apply(None), None)
        self.assertEqual(mod.apply("", "plain"), "")
        self.assertEqual(mod.apply(42, "plain"), 42)
        self.assertIn("Milestone moments",
                      mod.apply("Milestone moments", None))

    def test_text_selector(self):
        for old, new in mod.pairs():
            self.assertEqual(mod.text(old, "plain"), new)
            self.assertIs(mod.text(old), old)
        self.assertEqual(mod.text("unknown string", "plain"),
                         "unknown string")
        self.assertIsNone(mod.text(None, "plain"))

    def test_copy_is_ascii_and_nonempty(self):
        for old, new in mod.pairs():
            self.assertTrue(old and new)
            self.assertTrue(old.isascii())
            self.assertTrue(new.isascii())
            self.assertNotEqual(old, new)

    def test_section_lists_live_table(self):
        body = mod.section_html()
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", body)
        for _old, new in mod.pairs():
            self.assertIn(new, body)


class PlaincopyEffectTest(unittest.TestCase):
    def test_caller_history_plain_tone_restates_milestones(self):
        _tmp, db, _server, _out = make_module("plaincopy caller mod")
        _own_one(db)
        legacy = histmod.history_html(db)
        self.assertIn("Milestone moments", legacy)
        self.assertIn("First concept owned", legacy)
        plain = histmod.history_html(db, {"tone": ["plain"]})
        self.assertIn(">Milestones<", plain)
        # The milestone heading restates; the optout settings label keeps
        # its name (settings labels are out of scope), so exactly one
        # occurrence (the label) survives.
        self.assertEqual(plain.count("Milestone moments"),
                         legacy.count("Milestone moments") - 1)
        self.assertIn("First concept owned", plain)  # neutral kept
        # Legacy fallback pinned: absent/default/garbage tone keeps
        # the original celebration strings.
        self.assertIn("Milestone moments", histmod.history_html(db, {}))
        self.assertIn("Milestone moments",
                      histmod.history_html(db, {"tone": ["default"]}))
        self.assertIn("Milestone moments",
                      histmod.history_html(db, {"tone": ["verbose"]}))
        self.assertIn("Milestone moments",
                      histmod.history_html(db, None))


class PlaincopyShapeTest(unittest.TestCase):
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
        self.assertTrue(src.isascii())


if __name__ == "__main__":
    unittest.main()
