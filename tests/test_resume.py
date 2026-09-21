"""Resume interrupted sessions from History (I-48)."""
import unittest

from groundwork import resume as resumemod


class SessionKeyTest(unittest.TestCase):
    def test_groups_by_module_and_day(self):
        row = {"module_id": "m7", "reviewed_at": "2026-09-20T14:00:00Z"}
        self.assertEqual(resumemod.session_key(row), "m7:2026-09-20")

    def test_tuple_row(self):
        self.assertEqual(resumemod.session_key(("m7", "2026-09-20T14:00:00")),
                         "m7:2026-09-20")

    def test_same_module_different_days_differ(self):
        a = {"module_id": "m7", "reviewed_at": "2026-09-20T01:00:00"}
        b = {"module_id": "m7", "reviewed_at": "2026-09-21T01:00:00"}
        self.assertNotEqual(resumemod.session_key(a), resumemod.session_key(b))

    def test_malformed_rows_yield_empty(self):
        self.assertEqual(resumemod.session_key(None), "")
        self.assertEqual(resumemod.session_key({}), "")
        self.assertEqual(resumemod.session_key({"module_id": "m7"}), "")
        self.assertEqual(
            resumemod.session_key({"module_id": "m7",
                                   "reviewed_at": "not-a-date"}), "")

    def test_mid_cleaned_not_rejected(self):
        # Hostile chars are stripped; the surviving id still groups.
        self.assertEqual(
            resumemod.session_key({"module_id": "m7!!!",
                                   "reviewed_at": "2026-09-20"}),
            "m7:2026-09-20")


class ContinueUrlTest(unittest.TestCase):
    def test_builds_resume_link(self):
        self.assertEqual(resumemod.continue_url("m7:2026-09-20"),
                         "/due?resume=m7%3A2026-09-20")

    def test_accepts_row(self):
        row = {"module_id": "m7", "reviewed_at": "2026-09-20T01:00:00"}
        self.assertEqual(resumemod.continue_url(row),
                         "/due?resume=m7%3A2026-09-20")

    def test_hostile_keys_fall_back_to_due(self):
        for hostile in ("../../etc/passwd", "/reviews", "//evil.com/due",
                        "m7:2026-09-20#frag", "javascript:alert(1)",
                        "<script>", "", None, 42, "m7:not-a-day",
                        "m7:2026-09-20?x=1", "a b:2026-09-20"):
            self.assertEqual(resumemod.continue_url(hostile), "/due",
                             msg=repr(hostile))


class SessionCardsTest(unittest.TestCase):
    def test_narrows_to_module(self):
        cards = [{"id": "c1", "module_id": "m7"},
                 {"id": "c2", "module_id": "m8"}]
        out = resumemod.session_cards(cards, "m7:2026-09-20")
        self.assertEqual([c["id"] for c in out], ["c1"])

    def test_bad_key_returns_full_queue(self):
        cards = [{"id": "c1", "module_id": "m7"}]
        self.assertEqual(resumemod.session_cards(cards, "garbage"), cards)
        self.assertEqual(resumemod.session_cards(cards, ""), cards)

    def test_unfilterable_cards_returned_whole(self):
        cards = [{"id": "c1"}, {"id": "c2"}]
        self.assertEqual(resumemod.session_cards(cards, "m7:2026-09-20"),
                         cards)


class BannerTest(unittest.TestCase):
    def test_banner_renders(self):
        body = resumemod.resume_box_html("m7:2026-09-20", count=3,
                                         title="Fractions")
        self.assertIn("id='resume-box'", body)
        self.assertIn("Fractions", body)
        self.assertIn("3 cards still due", body)
        self.assertIn("href='/due'", body)

    def test_banner_escapes_title(self):
        body = resumemod.resume_box_html("m7:2026-09-20", title="<b>x</b>")
        self.assertNotIn("<b>x</b>", body)
        self.assertIn("&lt;b&gt;", body)

    def test_bad_key_no_banner(self):
        self.assertEqual(resumemod.resume_box_html("garbage"), "")
        self.assertEqual(resumemod.resume_box_html(None), "")

    def test_row_link(self):
        row = {"module_id": "m7", "reviewed_at": "2026-09-20T01:00:00"}
        link = resumemod.row_link(row)
        self.assertIn("/due?resume=", link)
        self.assertIn("continue session", link)
        self.assertEqual(resumemod.row_link({}), "")

    def test_section_anchor(self):
        body = resumemod.section_html()
        self.assertIn("id='status-b9-resume'", body)
        self.assertIn("groundwork/resume.py", body)


if __name__ == "__main__":
    unittest.main()
