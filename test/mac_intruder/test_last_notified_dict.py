import unittest
from datetime import datetime
from mac_intruder.last_notified_dict import LastNotifiedDict

# FILE: mac_intruder/test_last_notified_dict.py


class TestLastNotifiedDict(unittest.TestCase):

    def test_from_json_empty_dict(self):
        data = {}
        result = LastNotifiedDict.from_json(data)
        self.assertEqual(result, {})

    def test_from_json_valid_data(self):
        data = {
            "00:11:22:33:44:55": "2023-10-01T12:00:00",
            "66:77:88:99:AA:BB": "2023-10-02T13:30:00"
        }
        result = LastNotifiedDict.from_json(data)
        self.assertEqual(len(result), 2)
        self.assertEqual(result["00:11:22:33:44:55"], datetime.fromisoformat("2023-10-01T12:00:00"))
        self.assertEqual(result["66:77:88:99:aa:bb"], datetime.fromisoformat("2023-10-02T13:30:00"))

    def test_from_json_invalid_data(self):
        data = {
            "00:11:22:33:44:55": "invalid-datetime"
        }
        with self.assertRaises(ValueError):
            LastNotifiedDict.from_json(data)

if __name__ == "__main__":
    unittest.main()