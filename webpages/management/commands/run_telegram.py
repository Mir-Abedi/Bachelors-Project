from django.core.management.base import BaseCommand
from telegram.telegram_sender import run_telegram_bot

class Command(BaseCommand):
    help = 'start telegram bot'

    def handle(self, *args, **options):
        run_telegram_bot()

    