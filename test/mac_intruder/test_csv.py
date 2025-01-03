import os
import tempfile
import unittest
from mac_intruder.csv import write_known_devices

# FILE: mac_intruder/test_csv.py


class TestWriteKnownDevices(unittest.TestCase):

    def setUp(self):
        # Create a temporary file to act as our CSV file
        self.temp_file = tempfile.NamedTemporaryFile(delete=False)
        self.temp_file.close()

    def tearDown(self):
        # Remove the temporary file after each test
        os.remove(self.temp_file.name)

    def test_write_to_empty_csv(self):
        items = [("00:11:22:33:44:55", "192.168.1.2", "Device1")]
        write_known_devices(self.temp_file.name, items)
        
        with open(self.temp_file.name, "r") as file:
            lines = file.readlines()
        
        self.assertEqual(len(lines), 1)
        self.assertEqual(lines[0].strip(), str(items[0]))

    def test_write_to_csv_with_comments(self):
        with open(self.temp_file.name, "w") as file:
            file.write("# This is a comment\n")
        
        items = [("00:11:22:33:44:55", "192.168.1.2", "Device1")]
        write_known_devices(self.temp_file.name, items)
        
        with open(self.temp_file.name, "r") as file:
            lines = file.readlines()
        
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].strip(), "# This is a comment")
        self.assertEqual(lines[1].strip(), str(items[0]))

    def test_write_to_csv_with_existing_devices_and_comments(self):
        with open(self.temp_file.name, "w") as file:
            file.write("# This is a comment\n")
            file.write("00:11:22:33:44:55, 192.168.1.2, Device1\n")
        
        items = [("66:77:88:99:AA:BB", "192.168.1.3", "Device2")]
        write_known_devices(self.temp_file.name, items)
        
        with open(self.temp_file.name, "r") as file:
            lines = file.readlines()
        
        self.assertEqual(len(lines), 2)
        self.assertEqual(lines[0].strip(), "# This is a comment")
        self.assertEqual(lines[1].strip(), str(items[0]))

if __name__ == "__main__":
    unittest.main()