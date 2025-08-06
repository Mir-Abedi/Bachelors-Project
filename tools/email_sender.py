from utils import config
import os
from celery import shared_task
import smtplib
from email.message import EmailMessage

@shared_task
def send_email(body, subject, reciever):
    sender = config("HOTMAIL_SENDER")
    password = os.getenv("HOTMAIL_APP_PASSWORD")
    if not password:
        raise Exception("HOTMAIL_APP_PASSWORD not in env")

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = reciever
    msg["Subject"] = subject
    msg.set_content(body)

    try:
        with smtplib.SMTP("smtp.office365.com", 587) as server:
            server.starttls()
            server.login(sender, password)
            server.send_message(msg)
            print("Email sent successfully.")
    except Exception as e:
        print(f"Failed to send email: {e}")
        raise e