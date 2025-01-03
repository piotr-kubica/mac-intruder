import unittest
from datetime import datetime, timedelta
from unittest.mock import MagicMock, patch

from freezegun import freeze_time

from mac_intruder.last_notified_dict import LastNotifiedDict
from mac_intruder.mac_intruder import MacIntruder
from mac_intruder.network import NetworkDevice

# FILE: mac_intruder/test_mac_intruder.py


class TestMacIntruder(unittest.TestCase):

    @patch('mac_intruder.mac_intruder.scan_network')
    @patch('mac_intruder.mac_intruder.load_known_devices')
    @patch('mac_intruder.mac_intruder.write_known_devices')
    @patch('mac_intruder.mac_intruder.MacIntruder._save_last_notified', MagicMock())
    @patch('mac_intruder.mac_intruder.MacIntruder._save_last_email_check_time', MagicMock())
    @patch('mac_intruder.mac_intruder.GMailReader')
    @patch('mac_intruder.mac_intruder.GMailSender')
    @patch('mac_intruder.mac_intruder.EMAIL_CHECK_INTERVAL', 0)
    def test_no_new_devices_detected(self, MockGMailSender, MockGMailReader, mock_write_known_devices, mock_load_known_devices, mock_scan_network):
        mock_scan_network.return_value = []
        mock_load_known_devices.return_value = []
        mock_gmail_reader = MockGMailReader.return_value
        mock_gmail_reader.parse_unread_email_responses.return_value = []

        mac_intruder = MacIntruder()
        mac_intruder.scan_and_notify()

        mock_scan_network.assert_called_once()
        mock_load_known_devices.assert_called_once()
        mock_write_known_devices.assert_called_once()
        mock_gmail_reader.parse_unread_email_responses.assert_called_once()

    @patch('mac_intruder.mac_intruder.scan_network')
    @patch('mac_intruder.mac_intruder.load_known_devices')
    @patch('mac_intruder.mac_intruder.MacIntruder._load_last_notified')
    @patch('mac_intruder.mac_intruder.MacIntruder._save_last_notified', MagicMock())
    @patch('mac_intruder.mac_intruder.MacIntruder._save_last_email_check_time', MagicMock())
    @patch('mac_intruder.mac_intruder.write_known_devices')
    @patch('mac_intruder.mac_intruder.GMailReader')
    @patch('mac_intruder.mac_intruder.GMailSender')
    @patch('mac_intruder.mac_intruder.EMAIL_CHECK_INTERVAL', 0)
    def test_new_devices_detected_and_email_sent(self, MockGMailSender, MockGMailReader, mock_write_known_devices, mock_load_last_notified, mock_load_known_devices, mock_scan_network):
        mock_scan_network.return_value = [NetworkDevice(mac="00:11:22:33:44:55", ip="192.168.1.2", hostname="Device1")]
        mock_load_known_devices.return_value = []
        mock_load_last_notified.return_value = LastNotifiedDict()
        mock_gmail_reader = MockGMailReader.return_value
        mock_gmail_reader.parse_unread_email_responses.return_value = []

        mac_intruder = MacIntruder()
        mac_intruder.scan_and_notify()

        mock_scan_network.assert_called_once()
        mock_load_known_devices.assert_called_once()
        mock_write_known_devices.assert_called_once()
        mock_gmail_reader.parse_unread_email_responses.assert_called_once()
        MockGMailSender.return_value.send
        
    @freeze_time("2023-10-01 12:00:00")
    @patch('mac_intruder.mac_intruder.scan_network')
    @patch('mac_intruder.mac_intruder.load_known_devices')
    @patch('mac_intruder.mac_intruder.MacIntruder._load_last_notified')
    @patch('mac_intruder.mac_intruder.MacIntruder._save_last_notified', MagicMock())
    @patch('mac_intruder.mac_intruder.MacIntruder._save_last_email_check_time', MagicMock())
    @patch('mac_intruder.mac_intruder.write_known_devices')
    @patch('mac_intruder.mac_intruder.GMailReader')
    @patch('mac_intruder.mac_intruder.GMailSender')
    @patch('mac_intruder.mac_intruder.EMAIL_CHECK_INTERVAL', 0)
    def test_email_responses_with_new_macs_to_add(self, MockGMailSender, MockGMailReader, mock_write_known_devices, mock_load_last_notified, mock_load_known_devices, mock_scan_network):
        mock_scan_network.return_value = [NetworkDevice(mac="00:AA:22:33:44:55", ip="192.168.1.2", hostname="Device1")]
        mock_load_known_devices.return_value = []
        mock_load_last_notified.return_value = LastNotifiedDict({
            '00:AA:22:33:44:55': datetime(2023, 10, 1, 11, 30, 0)
        })
        mock_gmail_reader = MockGMailReader.return_value
        mock_gmail_reader.parse_unread_email_responses.return_value = [("Re: Detection", "add 00:AA:22:33:44:55")]

        mac_intruder = MacIntruder()
        mac_intruder.scan_and_notify()

        mock_scan_network.assert_called_once()
        mock_load_known_devices.assert_called_once()
        mock_write_known_devices.assert_called_once()
        mock_gmail_reader.parse_unread_email_responses.assert_called_once()
        MockGMailSender.return_value.send_email_with_attachment.assert_not_called()

    @patch('mac_intruder.mac_intruder.scan_network')
    @patch('mac_intruder.mac_intruder.load_known_devices')
    @patch('mac_intruder.mac_intruder.write_known_devices')
    @patch('mac_intruder.mac_intruder.MacIntruder._save_last_notified', MagicMock())
    @patch('mac_intruder.mac_intruder.MacIntruder._save_last_email_check_time', MagicMock())
    @patch('mac_intruder.mac_intruder.GMailReader')
    @patch('mac_intruder.mac_intruder.GMailSender')
    @patch('mac_intruder.mac_intruder.EMAIL_CHECK_INTERVAL', 0)
    def test_update_existing_devices_ip_and_hostname(self, MockGMailSender, MockGMailReader, mock_write_known_devices, mock_load_known_devices, mock_scan_network):
        mock_scan_network.return_value = [NetworkDevice(mac="00:11:22:33:44:55", ip="192.168.1.3", hostname="Device1")]
        mock_load_known_devices.return_value = [NetworkDevice(mac="00:11:22:33:44:55", ip="192.168.1.2", hostname="Device1")]
        mock_gmail_reader = MockGMailReader.return_value
        mock_gmail_reader.parse_unread_email_responses.return_value = []

        mac_intruder = MacIntruder()
        mac_intruder.scan_and_notify()

        mock_scan_network.assert_called_once()
        mock_load_known_devices.assert_called_once()
        mock_write_known_devices.assert_called_once()
        mock_gmail_reader.parse_unread_email_responses.assert_called_once()
        MockGMailSender.return_value.send_email_with_attachment.assert_not_called()

if __name__ == "__main__":
    unittest.main()
