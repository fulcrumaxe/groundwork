"""Delayed-retest engine: 7/30-day probe cards (F-51)."""
import unittest
from datetime import datetime, timedelta, timezone

from groundwork import retest as rmod


def iso(dt):
    return dt.astimezone(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


NOW = datetime(2026, 9, 21, 12, 0, 0, tzinfo=timezone.utc)


def card(cid, days_ago, owned=True, stability=30.0, probe_ago=None, **kw):
    c = {"card_id": cid, "owned": owned, "stability": stability,
         "last_review": iso(NOW - timedelta(days=days_ago)),
         "concept": "FSRS stability", "front": "What is S?",
         "back": "Memory strength in days."}
    if probe_ago is not None:
        c["last_probe"] = iso(NOW - timedelta(days=probe_ago))
    c.update(kw)
    return c


class ProbesDueTest(unittest.TestCase):
    def test_empty_list(self):
        self.assertEqual(rmod.probes_due([], NOW), [])
        self.assertEqual(rmod.probes_due(None, NOW), [])
        self.assertEqual(rmod.probes_due("nope", NOW), [])

    def test_seven_day_boundary(self):
        due = rmod.probes_due([card(1, 7)], NOW)
        self.assertEqual(len(due), 1)
        self.assertEqual(due[0], {"card_id": 1, "window": 7,
                                  "overdue_days": 0})
        just_short = rmod.probes_due([card(2, 6)], NOW)
        self.assertEqual(just_short, [])

    def test_thirty_day_boundary(self):
        due = rmod.probes_due([card(1, 30)], NOW)
        self.assertEqual(due[0]["window"], 30)
        self.assertEqual(due[0]["overdue_days"], 0)
        early = rmod.probes_due([card(2, 29)], NOW)
        self.assertEqual(early[0]["window"], 7)
        late = rmod.probes_due([card(3, 35)], NOW)
        self.assertEqual(late[0], {"card_id": 3, "window": 30,
                                   "overdue_days": 5})

    def test_intervening_probe_skips(self):
        c = card(1, 40, probe_ago=5)  # probed after the last review
        self.assertEqual(rmod.probes_due([c], NOW), [])
        old_probe = card(2, 40,
                         last_probe=iso(NOW - timedelta(days=50)))
        self.assertEqual(len(rmod.probes_due([old_probe], NOW)), 1)

    def test_unowned_or_unstable_skipped(self):
        self.assertEqual(rmod.probes_due([card(1, 40, owned=False)], NOW), [])
        self.assertEqual(rmod.probes_due([card(2, 40, stability=1.0)], NOW), [])
        self.assertEqual(rmod.probes_due([card(3, 40, stability="x")], NOW), [])

    def test_malformed_date_fail_closed(self):
        bad = card(1, 40, last_review="not-a-date")
        self.assertEqual(rmod.probes_due([bad], NOW), [])
        self.assertEqual(rmod.probes_due([{"nope": 1}, None, 42], NOW), [])
        # Garbage `now` falls back to the real clock but never raises;
        # the result is a plain list either way.
        res = rmod.probes_due([card(2, 40)], "garbage-now")
        self.assertIsInstance(res, list)

    def test_probe_card_names_concept(self):
        # Window derivation reads the real clock: date these cards
        # against real now so the test holds on any run date.
        real = datetime.now(timezone.utc)
        fresh = card(1, 10)
        fresh["last_review"] = iso(real - timedelta(days=10))
        p = rmod.probe_card(fresh)
        self.assertEqual(p["window"], 7)
        self.assertIn("FSRS stability", p["front"])
        self.assertIn("Retest (7d)", p["front"])
        old = card(2, 40)
        old["last_review"] = iso(real - timedelta(days=40))
        p30 = rmod.probe_card(old)
        self.assertEqual(p30["window"], 30)
        self.assertIn("Retest (30d)", p30["front"])
        weird = rmod.probe_card(None)
        self.assertEqual(weird["window"], 7)

    def test_never_raises(self):
        rmod.probes_due([None, {}, {"owned": True}], None)
        rmod.probe_card({})
        rmod.section_html()
        rmod.tour_entry()

    def test_section_and_tour(self):
        self.assertIn("id='status-b12-retest'", rmod.section_html())
        e = rmod.tour_entry()
        self.assertEqual(e["id"], "delayed-retest")
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], "status-b12-retest")

    def test_no_placeholders_in_shipped_module(self):
        import pathlib
        src = (pathlib.Path(__file__).resolve().parent.parent
               / "groundwork" / "retest.py").read_text(encoding="utf-8")
        for marker in ("[REDACTED]", "TODO", "FIXME", "XXX"):
            self.assertNotIn(marker, src)


if __name__ == "__main__":
    unittest.main()
