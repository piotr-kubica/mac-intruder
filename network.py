import subprocess
from dataclasses import dataclass

from logging import get_logger


@dataclass
class NetworkDevice:
    mac: str
    ip: str
    hostname: str

    def __str__(self):
        return f"{self.mac},{self.ip},{self.hostname}"


def scan_network() -> list[NetworkDevice]:
    """Scan the network and return a list of connected devices (MAC, IP, hostname)."""
    devices = []
    try:
        output = subprocess.check_output(
            ["sudo", "arp-scan", "-l"], universal_newlines=True
        )
        for line in output.split("\n"):
            if "\t" in line:
                parts = line.split("\t")
                devices.append(
                    NetworkDevice(
                        parts[1].strip().lower(), 
                        parts[0].strip(), 
                        parts[2].strip() if len(parts) > 2 else "Unknown"
                    )
                )
    except Exception as e:
        get_logger(__name__).info("Error scanning network: {e}")
    return devices