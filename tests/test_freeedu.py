"""Free-forever learner spotlight (F-148): live-LICENSE banner tests."""
import pathlib
import unittest
from unittest import mock

from groundwork import emoji as emojimod
from groundwork import freeedu as mod
from test_web import handler_for, make_module


def _live_text():
    return (pathlib.Path(mod.__file__).resolve().parent.parent
            / "LICENSE").read_text(encoding="utf-8")


class FreeeduUnitTest(unittest.TestCase):
    def test_live_license_recognized_with_all_markers(self):
        facts = mod.license_facts(_live_text())
        self.assertTrue(facts["present"])
        self.assertTrue(facts["recognized"])
        for key, _needle, _cite in mod.MARKERS:
            self.assertTrue(facts[key], key)

    def test_every_needle_quotes_live_license(self):
        live = _live_text()
        for key, needle, _cite in mod.MARKERS:
            self.assertIn(needle, live, key)

    def test_facts_empty_and_hostile(self):
        for bad in ("", 123, ["x"], {"a": 1}, b"bytes"):
            facts = mod.license_facts(bad)
            self.assertFalse(facts["present"], repr(bad))
            self.assertFalse(facts["recognized"], repr(bad))
        self.assertFalse(
            mod.license_facts("junk with no markers")["recognized"])

    def test_freedoms_gated_per_marker(self):
        rows = mod.freedoms(mod.license_facts(_live_text()))
        self.assertEqual(len(rows), 7)
        self.assertTrue(all(r["mark"] == "[x]" for r in rows))
        stripped = _live_text().replace("not impose a license fee",
                                        "PARTY TIME")
        rows2 = mod.freedoms(mod.license_facts(stripped))
        self.assertEqual(len(rows2), 6)
        self.assertFalse(any("No fee" in r["line"] for r in rows2))
        self.assertEqual(mod.freedoms(mod.license_facts("")), [])
        self.assertEqual(mod.freedoms("junk"), [])
        self.assertEqual(mod.freedoms({}), [])

    def test_banner_live_and_empty_states(self):
        out = mod.banner_html(_live_text())
        self.assertIn("id='freeedu'", out)
        self.assertIn("Free forever for learners", out)
        self.assertIn("LICENSE sec 10", out)
        self.assertIn("[x]", out)
        out.encode("ascii")
        self.assertEqual(mod.banner_html(""), "")
        self.assertEqual(mod.banner_html("junk with no markers"), "")
        title_only = "GNU AFFERO GENERAL PUBLIC LICENSE\nVersion 3\n"
        self.assertEqual(mod.banner_html(title_only), "")


class FreeeduEffectTest(unittest.TestCase):
    def test_history_page_shows_spotlight_when_licensed(self):
        _tmp, db, _server, _out = make_module("freeedu live mod")
        body = handler_for(db).history_html()
        self.assertIn("id='freeedu'", body)
        self.assertIn("Free forever for learners", body)

    def test_history_page_legacy_when_license_missing(self):
        _tmp, db, _server, _out = make_module("license legacy mod")
        with mock.patch("groundwork.freeedu.read_license_text",
                        return_value=""):
            self.assertEqual(mod.banner_html(), "")
            body = handler_for(db).history_html()
        self.assertNotIn("freeedu", body)


class FreeeduShapeTest(unittest.TestCase):
    def test_tour_entry_shape(self):
        e = mod.tour_entry()
        self.assertEqual(
            set(e), {"id", "kind", "title", "blurb", "path", "anchor"})
        self.assertEqual(e["kind"], "feature")
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], mod.STATUS_ANCHOR)

    def test_section_anchor_and_live_facts(self):
        html = mod.section_html()
        self.assertIn(f"id='{mod.STATUS_ANCHOR}'", html)
        self.assertIn("present: yes", html)

    def test_source_has_no_blocked_glyphs(self):
        src = pathlib.Path(mod.__file__).read_text(encoding="utf-8")
        self.assertEqual(emojimod.scan_text(src), [])


if __name__ == "__main__":
    unittest.main()
