"""Weekly lesson digest (I-149)."""
import unittest

from groundwork import weekdigest as mod

from test_web import handler_for, make_module


def _changes(n=3):
    return [{"concept": f"c{i}", "module": "M", "before": "a = 1\n",
             "after": "a = 2\n", "changed": 2} for i in range(n)]


class DigestTest(unittest.TestCase):
    def test_quiet_on_empty(self):
        self.assertEqual(mod.digest_html([]), "")
        self.assertEqual(mod.digest_html(None), "")

    def test_identical_pair_quiet(self):
        lessons = [{"concept_id": "c", "before": "x = 1\n",
                    "after": "x = 1\n"}]
        self.assertEqual(mod.changed_for(lessons), [])

    def test_changed_renders_counts(self):
        body = mod.digest_html(_changes(2))
        self.assertIn("Weekly lesson digest", body)
        self.assertIn("c0", body)
        self.assertIn("2 changed lines", body)
        self.assertIn("<h4>M</h4>", body)

    def test_cap(self):
        body = mod.digest_html(_changes(30), cap=25)
        self.assertEqual(body.count("<li>"), 25)

    def test_hostile_never_raises(self):
        self.assertEqual(mod.digest_html("nope"), "")
        self.assertEqual(mod.changed_for("nope"), [])
        self.assertEqual(mod.group_by_module(None), {})
        self.assertEqual(mod.block_html("/nonexistent.db"), "")

    def test_status_anchor_and_tour(self):
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'",
                      mod.section_html())
        entry = mod.tour_entry()
        self.assertEqual(entry["kind"], "improvement")
        self.assertEqual(entry["anchor"], mod.STATUS_ANCHOR)


class CallerEffectTest(unittest.TestCase):
    def test_history_legacy_identical_when_quiet(self):
        # Fixture lessons carry no before/after pairs: no digest.
        _tmp, db, _s, _out = make_module("weekdigest quiet")
        from groundwork import history as histmod
        body = histmod.history_html(db)
        self.assertNotIn("weekdigest", body)

    def test_block_lists_changes(self):
        changes = _changes(2)
        for c in changes:
            c["module"] = "Calc"
        body = mod.digest_html(changes)
        self.assertIn("Calc", body)
        self.assertIn("c1", body)


if __name__ == "__main__":
    unittest.main()
