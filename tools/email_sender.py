import yagmail
from utils import config
import os
from celery import shared_task
import smtplib
from email.mime.text import MIMEText

@shared_task
def send_email(body, subject, reciever):

    sender = config("HOTMAIL_SENDER")
    password = os.getenv("HOTMAIL_APP_PASSWORD")
    if not password:
        raise Exception("HOTMAIL_APP_PASSWORD not in env")

    msg = MIMEText(body)
    msg["Subject"] = subject
    msg["From"] = sender
    msg["To"] = reciever

    with smtplib.SMTP("smtp.office365.com", 587) as server:
        server.starttls()
        server.login(sender, password)
        server.send_message(msg)

    print("Email sent successfully.")