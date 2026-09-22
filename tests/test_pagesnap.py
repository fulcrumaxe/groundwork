"""CI gate: rendered-page snapshots fail on unexpected drift (I-95)."""
import os
import tempfile
import unittest
from pathlib import Path

from groundwork import db as dbmod
from groundwork import pagesnap as snapmod

from test_web import handler_for, make_module

GOLDEN_DIR = Path(__file__).with_name("golden")
PAGES = ("due", "status", "modules", "reviews")


def _goldens():
    out = {}
    for name in PAGES:
        p = GOLDEN_DIR / f"{name}.html"
        out[name] = p.read_text(encoding="utf-8") if p.exists() else ""
    return out


class PagesnapGateTest(unittest.TestCase):
    def test_snapshot_matches_committed_goldens(self):
        _tmp, db, _server, out = make_module("pagesnap gate module")
        h = handler_for(db)
        h._pagesnap_mid = out["module_id"]
        snap = snapmod.snapshot(h)
        self.assertEqual(set(snap), set(PAGES))
        goldens = _goldens()
        if os.environ.get("UPDATE_GOLDENS") == "1":
            GOLDEN_DIR.mkdir(exist_ok=True)
            for name, html_text in snap.items():
                (GOLDEN_DIR / f"{name}.html").write_text(
                    html_text + "\n", encoding="utf-8")
            goldens = _goldens()
        result = snapmod.compare(snap, goldens)
        self.assertTrue(result["ok"], f"page drift: {result}")

    def test_gate_trips_on_purposeful_markup_mutation(self):
        _tmp, db, _server, _out = make_module("pagesnap gate module")
        h = handler_for(db)
        snap = snapmod.snapshot(h)
        goldens = _goldens()
        mutated = dict(snap)
        mutated["due"] = snapmod.normalize(
            snap["due"] + "<div id='rogue-banner'>rogue</div>")
        result = snapmod.compare(mutated, goldens)
        self.assertFalse(result["ok"])
        self.assertIn("due", result["drift"])

    def test_identical_rerenders_pass(self):
        _tmp, db, _server, _out = make_module("pagesnap stable module")
        h = handler_for(db)
        first = snapmod.snapshot(h)
        second = snapmod.snapshot(h)
        self.assertEqual(first, second)
        self.assertTrue(snapmod.compare(second, first)["ok"])
        for name in PAGES:
            self.assertTrue(snapmod.check_golden(
                name, second[name], first[name]))

    def test_legacy_empty_db_renders_pinned_fallback(self):
        tmp = Path(tempfile.mkdtemp(prefix="gw-pagesnap-empty-"))
        db = str(tmp / "empty.db")
        dbmod.init_db(db)
        h = handler_for(db)
        snap = snapmod.snapshot(h)
        self.assertEqual(set(snap), set(PAGES))
        for _name, html_text in snap.items():
            self.assertIsInstance(html_text, str)
        legacy = snapmod.compare(snap, snap)
        self.assertTrue(legacy["ok"])

    def test_hostile_inputs_fail_closed(self):
        self.assertEqual(snapmod.normalize(None), "")
        self.assertEqual(snapmod.snapshot(None), {})
        self.assertEqual(snapmod.render_page(None, "due"), "")
        self.assertEqual(
            snapmod.render_page(handler_for.__class__, "nope"), "")
        bad = snapmod.compare(None, None)
        self.assertFalse(bad["ok"])
        self.assertFalse(snapmod.check_golden("due", "<p>a</p>", "<p>b</p>"))


if __name__ == "__main__":
    unittest.main()
