"""Recently visited strip (I-24): container, key, cap, escaping, fallback."""
import unittest

from groundwork import recent as recentmod


class ClipTest(unittest.TestCase):
    def test_caps_at_eight(self):
        entries = [{"id": f"m{i}"} for i in range(12)]
        self.assertEqual(len(recentmod.clip(entries)), 8)

    def test_dedupes_keeping_latest(self):
        entries = [{"id": "b"}, {"id": "a"}, {"id": "b"}]
        self.assertEqual([e["id"] for e in recentmod.clip(entries)], ["b", "a"])

    def test_bad_input_gives_empty(self):
        self.assertEqual(recentmod.clip(None), [])
        self.assertEqual(recentmod.clip("nope"), [])

    def test_custom_limit(self):
        entries = [{"id": f"m{i}"} for i in range(5)]
        self.assertEqual(len(recentmod.clip(entries, 3)), 3)


class StripTest(unittest.TestCase):
    def test_container_id_present(self):
        out = recentmod.strip_html()
        self.assertIn("id='recent'", out)
        self.assertIn("id='recent-list'", out)

    def test_localstorage_key_present(self):
        self.assertIn("gw-recent", recentmod.strip_html())

    def test_cap_logic_visible_in_script(self):
        out = recentmod.strip_html()
        self.assertIn("slice(0,N)", out)
        self.assertIn("var N=8", out)

    def test_escaping_via_textcontent_no_innerhtml(self):
        out = recentmod.strip_html()
        self.assertIn("textContent", out)
        self.assertNotIn("innerHTML", out)

    def test_empty_fallback_renders_no_entries(self):
        out = recentmod.strip_html()
        self.assertIn("id='recent-empty'", out)
        # Server emits zero links; JS fills them client-side.
        self.assertNotIn("<li>", out.split("</ul>")[0].split("<ul")[1] if "<ul" in out else out)


class RecordTest(unittest.TestCase):
    def test_record_uses_key_and_caps(self):
        js = recentmod.record_js("m1", "First mod")
        self.assertIn("gw-recent", js)
        self.assertIn("slice(0,N)", js)
        self.assertIn("localStorage.setItem", js)

    def test_record_escapes_hostile_mid(self):
        js = recentmod.record_js("m'</script><script>alert(1)", "t")
        self.assertNotIn("</script><script>", js)

    def test_record_empty_mid_noops(self):
        self.assertIn("if(!mid)return;", recentmod.record_js(""))


class StatusTest(unittest.TestCase):
    def test_section_html_anchor(self):
        body = recentmod.section_html()
        self.assertIn("id='status-b7-recent'", body)
        self.assertIn("recent.py", body)


if __name__ == "__main__":
    unittest.main()
