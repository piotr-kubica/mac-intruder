import unittest
from unittest.mock import patch, MagicMock
from mac_intruder.mailer import GMailReader

# FILE: mac_intruder/test_gmail.py


class TestGMailReader(unittest.TestCase):

    @patch('mac_intruder.gmail.imaplib.IMAP4_SSL')
    def test_no_unread_emails(self, mock_imap):
        # Mock the IMAP server response for no unread emails
        mock_mail = MagicMock()
        mock_mail.search.return_value = ("OK", [b""])
        mock_imap.return_value = mock_mail

        reader = GMailReader('test_user', 'test_pass', 'imap.gmail.com')
        result = reader.parse_unread_email_responses()
        
        self.assertEqual(result, [])
        mock_mail.search.assert_called_once_with(None, "UNSEEN")

    @patch('mac_intruder.gmail.imaplib.IMAP4_SSL')
    def test_unread_emails_from_other_addresses(self, mock_imap):
        # Mock the IMAP server response for unread emails from other addresses
        mock_mail = MagicMock()
        mock_mail.search.return_value = ("OK", [b"1"])
        mock_mail.fetch.return_value = ("OK", [(None, b"From: other@example.com\r\nSubject: Test\r\n\r\nBody")])
        mock_imap.return_value = mock_mail

        reader = GMailReader('test_user', 'test_pass', 'imap.gmail.com')
        result = reader.parse_unread_email_responses()
        
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0], ("Test", "Body"))
        mock_mail.search.assert_called_once_with(None, "UNSEEN")

    @patch('mac_intruder.gmail.imaplib.IMAP4_SSL')
    def test_unread_emails_from_same_address(self, mock_imap):
        # Mock the IMAP server response for unread emails from the same address
        mock_mail = MagicMock()
        mock_mail.search.return_value = ("OK", [b"1"])
        mock_mail.fetch.return_value = ("OK", [(None, b"From: test@example.com\r\nSubject: Test\r\n\r\nBody")])
        mock_imap.return_value = mock_mail

        # with patch('mac_intruder.gmail.EMAIL_USERNAME', 'test@example.com'):
        reader = GMailReader('test@example.com', 'test_pass', 'imap.gmail.com')
        result = reader.parse_unread_email_responses()
        
        self.assertEqual(result, [])
        mock_mail.search.assert_called_once_with(None, "UNSEEN")

    @patch('mac_intruder.gmail.imaplib.IMAP4_SSL')
    def test_multiple_unread_emails(self, mock_imap):
        # Mock the IMAP server response for multiple unread emails
        mock_mail = MagicMock()
        mock_mail.search.return_value = ("OK", [b"1 2"])
        mock_mail.fetch.side_effect = [
            ("OK", [(None, b"From: other1@example.com\r\nSubject: Test1\r\n\r\nBody1")]),
            ("OK", [(None, b"From: other2@example.com\r\nSubject: Test2\r\n\r\nBody2")])
        ]
        mock_imap.return_value = mock_mail

        reader = GMailReader('test_user', 'test_pass', 'imap.gmail.com')
        result = reader.parse_unread_email_responses()
        
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], ("Test1", "Body1"))
        self.assertEqual(result[1], ("Test2", "Body2"))
        mock_mail.search.assert_called_once_with(None, "UNSEEN")

if __name__ == "__main__":
    unittest.main()