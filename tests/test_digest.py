"""Daily digest (I-242): today's queue at a glance on Due."""
import unittest

from groundwork import digest as digestmod

from test_web import handler_for, make_module


class DigestTest(unittest.TestCase):
    def setUp(self):
        self.tmp, self.db, self.server, self.out = make_module("digest mod")

    def test_section_counts_and_suggests(self):
        out = digestmod.section_html(self.db)
        self.assertIn("id='digest'", out)
        self.assertIn("due now", out)
        self.assertIn("Start with", out)

    def test_due_page_opens_with_digest(self):
        out = handler_for(self.db).due_html()
        self.assertIn("id='digest'", out)
        self.assertLess(out.index("id='digest'"), out.index("<details"))


if __name__ == "__main__":
    unittest.main()
