import json
import logging
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict
from functools import reduce

from mac_intruder.constants import (
    EMAIL_PASSWORD,
    EMAIL_RECEPIENT,
    EMAIL_SUBJECT,
    EMAIL_TEMPLATE,
    EMAIL_TEMPLATE_POSTFIX,
    EMAIL_TEMPLATE_PREFIX,
    EMAIL_USERNAME,
    KNOWN_HOSTS,
    LAST_NOTIFIED_FILE,
    NOTIFY_INTERVAL,
    EMAIL_IMAP,
    EMAIL_CHECK_INTERVAL,
    EMAIL_CHECK_FILE
)
from mac_intruder.csv import load_known_devices, write_known_devices
from mac_intruder.gmail import GMailReader, GMailSender
from mac_intruder.last_notified_dict import LastNotifiedDict
from mac_intruder.logging import get_logger
from mac_intruder.network import NetworkDevice, scan_network

logger = get_logger(__name__, logging.INFO)


class MacIntruder:

    def __init__(self):
        self._known_devices: List[NetworkDevice] = []
        self._gmail_sender = GMailSender(EMAIL_USERNAME, EMAIL_PASSWORD)
        self._gmail_reader = GMailReader(EMAIL_USERNAME, EMAIL_PASSWORD, EMAIL_IMAP)

    def scan_and_notify(self):
        logger.info("Scanning local network...")
        scanned_devices: Dict[str, NetworkDevice] = {device.mac: device for device in scan_network()}
        known_devices: List[NetworkDevice] = self._load_known_devices()
        last_notified = self._load_last_notified()

        self._notify_new_devices(scanned_devices, known_devices, last_notified)
        devices_to_add = self._check_email_responses_for_devices(scanned_devices)
        known_devices.extend(devices_to_add)
        self._update_known_devices(scanned_devices, known_devices)
        self._save_known_devices(known_devices)


    def _notify_new_devices(self, scanned_devices, known_devices, last_notified):
        new_devices = self._filter_new_devices(scanned_devices, known_devices, last_notified)
        self._save_last_notified(last_notified)
        if new_devices:
            logger.info(f"New devices detected: {new_devices}")
            self._send_email(new_devices, KNOWN_HOSTS)
        else:
            logger.info("No new devices detected.")
        return new_devices
    
    def _check_email_responses_for_devices(self, scanned_devices):
        """
          Check for email responses with new hosts to add
        """
        devices_to_add = []
        current_dt = datetime.now()

        if (current_dt - self._load_last_email_check_time(current_dt)).total_seconds() >= EMAIL_CHECK_INTERVAL:
            self._save_last_email_check_time(current_dt)

            parsed_mail_content = [
                (subject, body) for subject, body in self._gmail_reader.parse_unread_email_responses()
            ]
            new_macs_from_email = [self._find_macs_to_add(body, subject) for subject, body in parsed_mail_content]
            new_macs_to_add = reduce(lambda acc, lst: acc + lst, new_macs_from_email, [])
            logger.info(f"Adding new devices for MACs: {new_macs_to_add}")

            for mac in new_macs_to_add:
                device = NetworkDevice(mac=mac, ip="Unknown", hostname="Unknown")
                devices_to_add.append(device)

                # Additionally update IP and hostname for scanned devices 
                if mac in scanned_devices.keys():
                    device.ip = scanned_devices[mac].ip
                    device.hostname = scanned_devices[mac].hostname

        return devices_to_add
    
    def _update_known_devices(self, scanned_devices, known_devices):
        """
        Update existing IP for known devices
        """
        for known_device in known_devices:
            if known_device.mac in scanned_devices.keys() and known_device.ip != scanned_devices[known_device.mac].ip:
                logger.info(f"Updating known scanned device {scanned_devices[known_device.mac]} \
                            has changed ip from {known_device.ip} to {scanned_devices[known_device.mac].ip}")
                known_device.ip = scanned_devices[known_device.mac].ip

    def _load_known_devices(self):
        return load_known_devices(KNOWN_HOSTS)

    def _save_known_devices(self, items):
        return write_known_devices(KNOWN_HOSTS, items)
    
    def _load_last_email_check_time(self, default_value=None):
        if os.path.exists(EMAIL_CHECK_FILE):
            with open(EMAIL_CHECK_FILE, "r") as file:
                # Read the first word or token
                content = file.read().split()[0]
                return datetime.fromisoformat(content)
        return default_value
    
    def _save_last_email_check_time(self, check_time):
        """
        Save the last email check time to a file.
        """
        with open(EMAIL_CHECK_FILE, "w") as file:
            file.write(check_time.isoformat())

    def _load_last_notified(self) -> LastNotifiedDict:
        """Load the last notified state from a JSON file."""
        if os.path.exists(LAST_NOTIFIED_FILE):
            with open(LAST_NOTIFIED_FILE, "r") as file:
                data = json.load(file)
                return LastNotifiedDict.from_json(data)
        return LastNotifiedDict()

    def _save_last_notified(self, last_notified: LastNotifiedDict):
        """Save the last notified state to a JSON file."""
        with open(LAST_NOTIFIED_FILE, "w") as file:
            json.dump(last_notified.to_json(), file)

    def _filter_new_devices(self, 
                            scaned_devices: Dict[str, NetworkDevice], 
                            known_devices: List[NetworkDevice], 
                            last_notified: LastNotifiedDict
                        ) -> List[NetworkDevice]:
        new_devices = []
        known_devices = known_devices or []
        known_devices_macs = [device.mac for device in known_devices]

        for mac, device in scaned_devices.items():
            if mac not in known_devices_macs:
                logger.info(f"MAC: {mac} not in known hosts.")

                last_notify_time_diff = 0
                interval = timedelta(seconds=NOTIFY_INTERVAL)
                now = datetime.now()

                if mac in last_notified:
                    last_notify_time_diff = now - last_notified.get(mac)

                    if last_notify_time_diff > interval:
                        last_notified[mac] = now
                        new_devices.append(device)
                else:
                    last_notified[mac] = now
                    new_devices.append(device)
            else: 
                if mac in last_notified:
                    del last_notified[mac]
        
        return new_devices

    def _send_email(self, new_devices: list[NetworkDevice], known_devices: str):
        formatted_devices = "\n".join([
            EMAIL_TEMPLATE.format(device.mac, device.ip, device.hostname) 
            for device in new_devices])
        body = f"{EMAIL_TEMPLATE_PREFIX}\n{formatted_devices}\n{EMAIL_TEMPLATE_POSTFIX}"
        self._gmail_sender.send_email_with_attachment(
            topic=EMAIL_SUBJECT,
            message=body,
            recepient=EMAIL_RECEPIENT,
            file_path=known_devices,
            is_binary=False,
        )

    def _find_macs_to_add(self, body, subject) -> List[str]:
        if f"Re: {EMAIL_SUBJECT}" not in subject:
            logger.info(f"No emails found matching response to detection email.")
            return []

        mac_to_add = []

        # Parse the email for all occurrences of 'add <mac_addr>'
        # Regex pattern to match "add" followed by a valid MAC address
        mac_address_pattern = r"add\s+([0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2}:[0-9A-Fa-f]{2})"

        # Use re.findall to extract all matching MAC addresses
        matched_mac_addresses = re.findall(mac_address_pattern, body)

        if matched_mac_addresses:
            for mac_addr in matched_mac_addresses:
                mac_to_add.append(mac_addr)

        return mac_to_add
