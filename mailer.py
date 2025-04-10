import subprocess
import mimetypes
from email.message import EmailMessage
from email.header import decode_header
from constants import MAILDIR_PATH,EMAIL_RECEPIENT,EMAIL_SUBJECT,EMAIL_CHECK_FILE,KNOWN_HOSTS
from log import get_logger
import os
from datetime import datetime
from csv_devices import load_known_devices, write_known_devices
from email import message_from_binary_file

logger = get_logger(__name__)

RELEVANT_SENDER = EMAIL_RECEPIENT
RELEVANT_SUBJECT = EMAIL_SUBJECT


class Mailer:
    def __init__(self, gmail_user):
        self.gmail_user = gmail_user

    def _create_message(self, subject, body, recipient, cc=None):
        msg = EmailMessage()
        msg["Subject"] = subject
        msg["From"] = self.gmail_user
        msg["To"] = recipient
        if cc:
            msg["Cc"] = cc
        msg.set_content(body)
        return msg

    def _create_message_with_attachment(self, subject, body, recipient, file_path, cc=None):
        msg = self._create_message(subject, body, recipient, cc)

        # Guess MIME type
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        maintype, subtype = mime_type.split('/', 1)

        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
                filename = file_path.split('/')[-1]
                msg.add_attachment(file_data, maintype=maintype, subtype=subtype, filename=filename)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise

        return msg

    def _send(self, msg, recipient, cc=None, bcc=None):
        # Combine all actual recipients for msmtp CLI
        all_recipients = [recipient]
        if cc:
            all_recipients += [cc] if isinstance(cc, str) else cc
        if bcc:
            all_recipients += [bcc] if isinstance(bcc, str) else bcc

        try:
            logger.info("Sending email via msmtp...")
            process = subprocess.Popen(
                ['msmtp', '--debug'] + all_recipients,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE
            )
            stdout, stderr = process.communicate(msg.as_bytes())
            if process.returncode != 0:
                logger.error(f"msmtp failed: {stderr.decode()}")
            else:
                logger.info("Email sent successfully!")
        except Exception as e:
            logger.error(f"Failed to send email: {e}")

    def _parse_maildir_responses(self):
        """
        Read local maildir and return relevant (subject, body) pairs.
        """
        results = []

        for filename in os.listdir(MAILDIR_PATH):
            filepath = os.path.join(MAILDIR_PATH, filename)
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
