"""Pretty 404 (I-13): unknown paths get links and a repo search."""
import unittest

from groundwork import errors as errmod


class NotFoundTest(unittest.TestCase):
    def test_shows_path_links_and_search(self):
        out = errmod.not_found_html("/nope")
        self.assertIn("id='not-found'", out)
        self.assertIn("/nope", out)
        for href in ("/", "/due", "/modules", "/reviews", "/tour", "/status"):
            self.assertIn(f"href='{href}'", out)
        self.assertIn("action='/modules'", out)
        self.assertIn("name='repo'", out)

    def test_detail_optional_and_escaped(self):
        out = errmod.not_found_html("/x", "Unknown <module>.")
        self.assertIn("Unknown &lt;module&gt;.", out)
        self.assertNotIn("<module>", out)


if __name__ == "__main__":
    unittest.main()
