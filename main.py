import logging
import os
import csv
from dotenv import load_dotenv

from mac_intruder.constants import KNOWN_HOSTS
from mac_intruder.logging import get_logger
from mac_intruder.mac_intruder import MacIntruder

# Load environment variables from .env file
load_dotenv()

logger = get_logger(__name__, logging.INFO)


def create_known_hosts_file(known_hosts_file_path: str):
    """Create the known hosts file if it does not exist."""
    if not os.path.exists(known_hosts_file_path):
        with open(known_hosts_file_path, mode="w", newline="") as file:
            writer = csv.DictWriter(file, fieldnames=["MAC", "IP", "hostname"])
            writer.writeheader()


if __name__ == "__main__":
    logger.info("Starting mac-intruder scan")
    create_known_hosts_file(KNOWN_HOSTS)
    mac_intruder = MacIntruder()
    mac_intruder.scan_and_notify()
    logger.info("mac-intruder scan ended successfully")