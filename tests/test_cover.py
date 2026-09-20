"""Cover colors from repo hash (I-74)."""
import unittest

from groundwork import cover as covermod


class CoverTest(unittest.TestCase):
    def test_stable_hex(self):
        c1 = covermod.cover_color("my-repo")
        c2 = covermod.cover_color("my-repo")
        self.assertEqual(c1, c2)
        self.assertRegex(c1, r"^#[0-9a-f]{6}$")

    def test_distinct_repos_differ(self):
        colors = {covermod.cover_color(f"repo-{i}") for i in range(10)}
        self.assertGreater(len(colors), 1)

    def test_html_swatch(self):
        body = covermod.cover_html("my-repo")
        self.assertIn("id='cover'", body)
        self.assertIn("background:", body)


if __name__ == "__main__":
    unittest.main()
