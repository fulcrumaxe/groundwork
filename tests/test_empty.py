"""Empty states with next actions (I-12)."""
import unittest

from groundwork import empty as emptymod


class EmptyStateTest(unittest.TestCase):
    def test_known_pages_have_next_action(self):
        for page in ("due", "modules", "history", "journal"):
            body = emptymod.empty_state(page)
            self.assertIn("id='empty'", body)
            self.assertIn("<a href=", body)

    def test_unknown_page_falls_back(self):
        body = emptymod.empty_state("nope")
        self.assertIn("id='empty'", body)
        self.assertIn("<a href", body)


if __name__ == "__main__":
    unittest.main()
