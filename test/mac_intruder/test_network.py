import unittest
from unittest.mock import patch
from mac_intruder.network import scan_network, NetworkDevice

# FILE: mac_intruder/test_network.py


class TestScanNetwork(unittest.TestCase):

    @patch('mac_intruder.network.subprocess.check_output')
    def test_no_devices_found(self, mock_check_output):
        mock_check_output.return_value = ""
        result = scan_network()
        self.assertEqual(result, [])

    @patch('mac_intruder.network.subprocess.check_output')
    def test_multiple_devices_found(self, mock_check_output):
        mock_check_output.return_value = (
            "192.168.1.2\t00:11:22:33:44:55\tDevice1\n"
            "192.168.1.3\t66:77:88:99:AA:BB\tDevice2\n"
        )
        result = scan_network()
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0], NetworkDevice("00:11:22:33:44:55", "192.168.1.2", "Device1"))
        self.assertEqual(result[1], NetworkDevice("66:77:88:99:aa:bb", "192.168.1.3", "Device2"))

    @patch('mac_intruder.network.subprocess.check_output')
    def test_error_during_scan(self, mock_check_output):
        mock_check_output.side_effect = Exception("Scan error")
        result = scan_network()
        self.assertEqual(result, [])

if __name__ == "__main__":
    unittest.main()