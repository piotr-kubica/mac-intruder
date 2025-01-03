import email
import imaplib
import smtplib
import time
from email import encoders
from email.mime.base import MIMEBase
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.policy import default
from mac_intruder.logging import get_logger

logger = get_logger(__name__)


class GMailReader:

    def __init__(self, user, password, email_imap) -> None:
        self.gmail_user = user
        self.gmail_pass = password
        self.imap = email_imap
    
    def parse_email_body(self, email_msg):
        body = ""
        if email_msg.is_multipart():
            for part in email_msg.walk():
                if part.get_content_type() == "text/plain":
                    body = part.get_payload(decode=True).decode()
        else:
            body = email_msg.get_payload(decode=True).decode()

        return body

    def parse_unread_email_responses(self):
        try:
            # Connect to Gmail inbox
            mail = imaplib.IMAP4_SSL(self.imap)
            mail.login(self.gmail_user, self.gmail_pass)
            mail.select("inbox")

            # Search for unread emails
            status, messages = mail.search(None, "UNSEEN")
            if status != "OK":
                logger.info("No new emails found.")
                return []

            logger.info(f"Checking {len(messages[0].split())} messages for new known host.")
            mail_content = []

            # Process each email
            for num in messages[0].split():
                status, data = mail.fetch(num, "(RFC822)")
                if status != "OK":
                    continue

                raw_email = data[0][1]
                email_msg = email.message_from_bytes(raw_email, policy=default)
                from_address = email.utils.parseaddr(email_msg["From"])[1]

                # Skip emails from own address
                if from_address == self.gmail_user:
                    continue

                subject = email_msg["Subject"]
                body = self.parse_email_body(email_msg)
                mail_content.append((subject, body))

            return mail_content
        except Exception as e:
            logger.info(f"Error reading emails: {e}")
            return []
        finally:
            mail.close()
            mail.logout()


class GMailSender:
    default_retry = 2
    default_retry_sleep = 30
    default_timeout = 15

    def __init__(self, user, password) -> None:
        self.gmail_user = user
        self.gmail_pass = password

    def send_email(self, topic="", message="", recepient=""):
        to = recepient
        bcc = cc = ''
        msg = self._create_message(topic, message, recepient, cc)
        self._send(msg, self.gmail_user, to, cc, bcc)

    def send_email_with_attachment(self, topic="", message="", recepient="", file_path="", is_binary=True):
        to = recepient
        bcc = cc = ''
        msg = self._create_message_with_attachment(topic, message, recepient, cc, file_path, is_binary)
        self._send(msg, self.gmail_user, to, cc, bcc)

    def _create_message(self, topic, message, recepient, cc):
        sent_from = self.gmail_user
        subject = topic
        send_to = [recepient]
        send_cc = [cc]

        # create message - the correct MIME type is multipart/alternative.
        msg = MIMEMultipart('alternative')
        msg['Subject'] = subject
        msg['From'] = sent_from
        msg['To'] = ", ".join(send_to)
        msg['cc'] = ", ".join(send_cc)
        text = message
        mime_text = MIMEText(text, 'plain')
        msg.attach(mime_text)
        return msg

    def _create_message_with_attachment(self, topic, message, recepient, cc, file_path, is_binary):
        # Reuse _create_message to build the base message
        msg = self._create_message(topic, message, recepient, cc)

        # Attach the file
        try:
            with open(file_path, "rb" if is_binary else "r") as attachment:
                if is_binary:
                    part = MIMEBase("application", "octet-stream")
                    part.set_payload(attachment.read())
                    encoders.encode_base64(part)
                else:
                    part = MIMEText(attachment.read(), 'plain')

                # Add header as key/value pair to attachment part
                part.add_header(
                    "Content-Disposition",
                    f"attachment; filename={file_path.split('/')[-1]}",
                )

                # Attach the file to the message
                msg.attach(part)
        except FileNotFoundError:
            logger.error(f"File not found: {file_path}")
            raise

        return msg

    def _send(self, msg, _from, to, cc, bcc):
        retry = initial_retry_cnt = self.default_retry
        while(retry > 0):
            try:
                logger.info("Sending message: " + msg.as_string())
                server = smtplib.SMTP_SSL('smtp.gmail.com', 465, None, None, None, timeout=10)
                server.ehlo()
                server.login(self.gmail_user, self.gmail_pass)
                server.sendmail(_from, to + cc + bcc, msg.as_string())
                server.close()
                logger.info("Message sent successfully!")
                retry = 0
            except OSError as ex:
                logger.info("Message failed to send! Reason: " + str(ex))
                retry -= 1
                logger.info("Retry " + str(initial_retry_cnt - retry) + " of " + str(initial_retry_cnt))
                time.sleep(self.default_retry_sleep)
