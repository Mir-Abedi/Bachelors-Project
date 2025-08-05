import yagmail
from utils import config
import os
from celery import shared_task

@shared_task
def send_email(body, subject, reciever):
    gmail = config("GMAIL")
    gmail_app_password = os.getenv("GMAIL_APP_PASSWORD")
    if not gmail_app_password:
        raise Exception("GMAIL_APP_PASSWORD not in env")
    yag = yagmail.SMTP(gmail, gmail_app_password)
    yag.send(to=reciever, subject=subject, contents=body)