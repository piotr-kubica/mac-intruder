import os
from typing import List

from mac_intruder.network import NetworkDevice


def load_known_devices(known_devices_csv: str) -> list[str]:
    """Load the predefined device list from a CSV file, ignoring comments and stripping spaces."""
    devices_list = list()
    if os.path.exists(known_devices_csv):
        with open(known_devices_csv, mode="r") as file:
            for line in file:

                # Skip lines starting with '#' and empty lines
                if line.strip() and not line.startswith("#"):
                    mac, ip, hostname = map(str.strip, line.split(","))
                    devices_list.append(NetworkDevice(mac=mac.lower(), ip=ip, hostname=hostname))
    return devices_list


def write_known_devices(csv: str, items: List[tuple]):
    str_lines: List[str] = []

    if os.path.exists(csv):
        with open(csv, mode="r") as file:
            for line in file:
                if line.strip().startswith("#"):
                    str_lines.append(line.strip())

    for item in items:
        str_lines.append(str(item).strip())

    with open(csv, mode="w") as file:
        for line in str_lines:
            file.write(f"{line}\n")