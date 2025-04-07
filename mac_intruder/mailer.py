import subprocess
import mimetypes
from email.message import EmailMessage
import logging

logger = logging.getLogger(__name__)


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
