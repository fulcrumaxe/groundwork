"""Motion budget: total animation <=300ms, all reduced-motion gated (I-98)."""
import re
import unittest
from pathlib import Path

from groundwork import motion as momod


def _durations_ms(css):
    out = [float(m.group(1)) for m in
           re.finditer(r"(\d+(?:\.\d+)?)\s*ms", css)]
    for m in re.finditer(r"animation:[^;{}]*?(\d+(?:\.\d+)?)s(?![\d.]*\s*ms)", css):
        out.append(float(m.group(1)) * 1000.0)
    return out


class MotionTest(unittest.TestCase):
    def test_effect_every_shipped_keyframe_duration_within_budget(self):
        css = momod.motion_css()
        self.assertIn("@keyframes", css)
        durs = _durations_ms(css)
        self.assertTrue(durs)
        for ms in durs:
            self.assertLessEqual(ms, 300)

    def test_effect_every_keyframe_reduced_motion_gated(self):
        css = momod.motion_css()
        self.assertIn("prefers-reduced-motion", css)
        tail = css.split("prefers-reduced-motion")[-1].replace(" ", "")
        self.assertIn("animation:none", tail)
        names = re.findall(r"@keyframes\s+([\w-]+)", css)
        self.assertTrue(names)
        for n in names:
            self.assertIn(n, css.split("prefers-reduced-motion")[0])

    def test_effect_page_head_css_within_budget(self):
        # Real caller: the page-chrome head CSS wire on every page.
        from groundwork import web as webmod
        res = momod.audit_css(webmod.CSS)
        self.assertEqual(res["over"], [])
        self.assertTrue(res["ok"], f"head CSS over motion budget: {res}")

    def test_effect_planted_400ms_fixture_fails_audit(self):
        bad = ("@keyframes gw-evil{from{opacity:0}to{opacity:1}}"
               ".evil{animation:gw-evil 400ms ease-out both}")
        res = momod.audit_css(bad)
        self.assertFalse(res["ok"])
        self.assertTrue(res["over"])
        good = momod.audit_css(momod.motion_css())
        self.assertTrue(good["ok"])
        self.assertEqual(good["over"], [])
        self.assertEqual(good["ungated"], [])

    def test_effect_ungated_keyframe_fails_audit(self):
        bad = ("@keyframes gw-lonely{from{opacity:0}to{opacity:1}}"
               ".lonely{animation:gw-lonely 200ms ease-out both}")
        self.assertFalse(momod.audit_css(bad)["ok"])

    def test_legacy_no_data_path_pinned_as_fallback(self):
        for empty in ("", "   ", None, 0, object()):
            res = momod.audit_css(empty)
            self.assertEqual(res, {"over": [], "ungated": [], "ok": True})
        self.assertIsInstance(momod.motion_css(), str)
        self.assertIn("opacity:1", momod.motion_css())

    def test_helpers_fail_closed_never_raise(self):
        for bad in (None, "fast", True, -5, 9999, object()):
            ms = momod.duration_ms(bad)
            self.assertGreaterEqual(ms, 0)
            self.assertLessEqual(ms, 300)
        self.assertEqual(momod.budget_ms("nope"), 250)
        self.assertEqual(momod.budget_ms(None), 250)

    def test_raw_declarations_only_no_tags_or_js(self):
        blob = (momod.motion_css() + momod.section_html()).lower()
        self.assertNotIn("<style", blob)
        self.assertNotIn("<script", blob)
        src = Path(__file__).resolve().parent.parent.joinpath(
            "groundwork", "motion.py").read_text(encoding="utf-8").lower()
        # Prose may name the tag in backticks; only real emissions count.
        code = src.replace("`<style>`", "")
        for marker in ("document.", "addeventlistener", "settimeout",
                       "\"<style", "'<style"):
            self.assertNotIn(marker, code)

    def test_section_html_anchor(self):
        self.assertIn("id='status-b18-motion'", momod.section_html())

    def test_tour_entry_shape(self):
        e = momod.tour_entry()
        self.assertEqual(e["id"], "motion-budget")
        self.assertEqual(e["kind"], "improvement")
        self.assertTrue(e["title"] and e["blurb"])
        self.assertEqual(e["path"], "/status")
        self.assertEqual(e["anchor"], "status-b18-motion")


if __name__ == "__main__":
    unittest.main()
