"""Exit ticket renderer (I-113)."""
import unittest

from groundwork import exitticket as etmod


class TicketTest(unittest.TestCase):
    def test_ticket_form(self):
        body = etmod.ticket_html("Loops", "What does break do?")
        self.assertIn("id='exitticket'", body)
        self.assertIn("ungraded", body)
        self.assertIn("What does break do?", body)

    def test_blank_renders_empty(self):
        self.assertEqual(etmod.ticket_html("", ""), "")


if __name__ == "__main__":
    unittest.main()
