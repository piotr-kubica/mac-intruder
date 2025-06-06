import json
import os
import re
from datetime import datetime, timedelta
from typing import List, Dict
from functools import reduce
from constants import (
    EMAIL_RECEPIENT,
    EMAIL_SUBJECT,
    EMAIL_TEMPLATE,
    EMAIL_TEMPLATE_POSTFIX,
    EMAIL_TEMPLATE_PREFIX,
    EMAIL_USERNAME,
    KNOWN_HOSTS,
    LAST_NOTIFIED_FILE,
    NOTIFY_INTERVAL,
    EMAIL_CHECK_INTERVAL,
    EMAIL_CHECK_FILE,
    ENABLE_MAIL_RESPONSE_DEVICE_ADDING,
    MAILDIR_PATH
)
from csv_devices import load_known_devices, write_known_devices
from mailer import Mailer
from last_notified_dict import LastNotifiedDict
from log import get_logger
from network import NetworkDevice, scan_network
from email import message_from_binary_file
from email.header import decode_header

logger = get_logger(__name__)

RELEVANT_SENDER = EMAIL_RECEPIENT
RELEVANT_SUBJECT = EMAIL_SUBJECT


class MacIntruder:

    def __init__(self):
        self._known_devices: List[NetworkDevice] = []
        self._mailer = Mailer(EMAIL_USERNAME)

    def scan_and_notify(self):
        logger.info("Scanning local network...")
        scanned_devices: Dict[str, NetworkDevice] = {device.mac: device for device in scan_network()}
        known_devices: List[NetworkDevice] = self._load_known_devices()
        last_notified = self._load_last_notified()
        new_devices = self._filter_new_devices(scanned_devices, known_devices, last_notified)
        self._save_last_notified(last_notified)
        if new_devices:
            logger.info(f"New devices detected: {new_devices}")
            self._send_email(new_devices, KNOWN_HOSTS)
        else:
            logger.info("No new devices detected.")

        if bool(ENABLE_MAIL_RESPONSE_DEVICE_ADDING):
            # TODO run mbsync gmail
            devices_to_add = self._check_email_responses_for_devices(scanned_devices)
            for device in devices_to_add:
                if device.mac not in [known_device.mac for known_device in known_devices]:
                    logger.info(f"Adding new devices for MACs: {device.mac}")
                    known_devices.append(device)
            self._update_known_devices(scanned_devices, known_devices)
            self._save_known_devices(known_devices)
        return new_devices

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

    def _send_email(self, new_devices: list[NetworkDevice], known_devices_path: str):
        logger.info("Creating email with new devices.")
        formatted_devices = "\n".join([
            EMAIL_TEMPLATE.format(device.mac, device.ip, device.hostname) 
            for device in new_devices])
        body = f"{EMAIL_TEMPLATE_PREFIX}\n{formatted_devices}\n{EMAIL_TEMPLATE_POSTFIX}"

        msg = self._mailer._create_message_with_attachment(
            subject=EMAIL_SUBJECT,
            body=body,
            recipient=EMAIL_RECEPIENT,
            file_path=known_devices_path
        )
        logger.info(f"Sending email to {EMAIL_RECEPIENT} with new devices.")
        self._mailer._send(msg, EMAIL_RECEPIENT)

    def _check_email_responses_for_devices(self, scanned_devices):
        """
          Check for email responses with new hosts to add
        """
        logger.info("Checking email responses with new hosts to add...")
        devices_to_add = []
        parsed_mail_content = [
            (subject, body) for subject, body in self._parse_maildir_responses()
        ]
        new_macs_from_email = [self._find_macs_to_add(body, subject) for subject, body in parsed_mail_content]
        new_macs_to_add = set(reduce(lambda acc, lst: acc + lst, new_macs_from_email, []))

        for mac in new_macs_to_add:
            device = NetworkDevice(mac=mac, ip="Unknown", hostname="Unknown")
            devices_to_add.append(device)

            # Additionally update IP and hostname for scanned devices 
            if mac in scanned_devices.keys():
                device.ip = scanned_devices[mac].ip
                device.hostname = str(scanned_devices[mac].hostname).replace(",", "")

        return devices_to_add
        
    def _parse_maildir_responses(self):
        """
        Read local maildir and return relevant (subject, body) pairs.
        """
        logger.info("Reading local maildir...")
        results = []
        current_time = datetime.now()

        # Expand the MAILDIR_PATH to handle '~'
        maildir_path = os.path.expanduser(MAILDIR_PATH)

        for filename in os.listdir(maildir_path):
            filepath = os.path.join(maildir_path, filename)
            file_mod_time = datetime.fromtimestamp(os.path.getmtime(filepath))

            if (current_time - file_mod_time).total_seconds() > EMAIL_CHECK_INTERVAL * 2:
                continue  # Skip files older than EMAIL_CHECK_INTERVAL * 2

            try:
                with open(filepath, "rb") as f:
                    msg = message_from_binary_file(f)
                    sender = msg.get("From", "")
                    subject_raw = msg.get("Subject", "")
                    subject = decode_header(subject_raw)[0][0]
                    if isinstance(subject, bytes):
                        subject = subject.decode("utf-8", errors="replace")

                    if (
                        RELEVANT_SENDER in sender.lower() and
                        RELEVANT_SUBJECT.lower() in subject.lower()
                    ):
                        # Get plain text body
                        if msg.is_multipart():
                            for part in msg.walk():
                                if part.get_content_type() == "text/plain":
                                    body = part.get_payload(decode=True).decode(errors="replace")
                                    results.append((subject, body))
                                    break
                        else:
                            body = msg.get_payload(decode=True).decode(errors="replace")
                            results.append((subject, body))
            except Exception as e:
                logger.warning(f"Failed to parse {filepath}: {e}")
                
        return results

    def _find_macs_to_add(self, body, subject) -> List[str]:
        if f"Re: {EMAIL_SUBJECT}" not in subject:
            logger.info("No emails found matching response to detection email.")
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

