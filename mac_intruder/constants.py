import os

# Configuration
KNOWN_HOSTS = os.getenv("KNOWN_HOSTS", "known-hosts.csv")
LAST_NOTIFIED_FILE = os.getenv("LAST_NOTIFIED_FILE", "last_notified.json")
EMAIL_SMTP = os.getenv("EMAIL_SMTP", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_IMAP = os.getenv("EMAIL_IMAP", "imap.gmail.com")
EMAIL_USERNAME = os.getenv("EMAIL_USERNAME", "your_email@gmail.com")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD", "your_app_password")
NOTIFY_INTERVAL = int(os.getenv("NOTIFY_INTERVAL", 86400))  # 24 hours
EMAIL_CHECK_INTERVAL = int(os.getenv("EMAIL_CHECK_INTERVAL", 21600))  # 6 hours in seconds
EMAIL_CHECK_FILE = os.getenv("EMAIL_CHECK_FILE", "last_email_checked.txt")
EMAIL_RECEPIENT = os.getenv("EMAIL_RECEPIENT", "receiver_email@gmail.com")

# Email template
EMAIL_SUBJECT = "New Device Detected on LAN"
EMAIL_TEMPLATE_PREFIX = "New devices detected on your LAN:"
EMAIL_TEMPLATE = "{0}, {1}, {2}"
EMAIL_TEMPLATE_POSTFIX = "List of known devices attached for reference."