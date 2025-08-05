import yagmail
from utils import config
import os
from celery import shared_task
import smtplib
import socket

@shared_task
def send_email(body, subject, reciever):
    sender = config("HOTMAIL_SENDER")
    password = os.getenv("HOTMAIL_APP_PASSWORD")
    if not password:
        raise Exception("HOTMAIL_APP_PASSWORD not in env")

    # Force IPv4 resolution of SMTP host
    smtp_host = "smtp.office365.com"
    smtp_port = 587
    ipv4_host = socket.gethostbyname(smtp_host)

    with smtplib.SMTP(ipv4_host, smtp_port) as server:
        server.starttls()
        server.login(sender, password)
        message = f"Subject: {subject}\n\n{body}"
        server.sendmail(sender, reciever, message)

    print("Email sent successfully.")