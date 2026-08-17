import os
import smtplib
from email.mime.text import MIMEText

GMAIL_ADDRESS = os.environ["GMAIL_ADDRESS"]
GMAIL_APP_PASSWORD = os.environ["GMAIL_APP_PASSWORD"]
TO_EMAIL = os.environ.get("TO_EMAIL", GMAIL_ADDRESS)


def main():
    msg = MIMEText("This is a test email from the contest-reminder test script. If you got this, your Gmail SMTP setup works.")
    msg["Subject"] = "Contest Reminder - Test Email"
    msg["From"] = GMAIL_ADDRESS
    msg["To"] = TO_EMAIL

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(GMAIL_ADDRESS, GMAIL_APP_PASSWORD)
        server.sendmail(GMAIL_ADDRESS, [TO_EMAIL], msg.as_string())

    print(f"Test email sent to {TO_EMAIL}")


if __name__ == "__main__":
    main()
