import pyrogram
import os
from celery import shared_task
from utils import config
from webpages.models import Author
import logging

logging.basicConfig(level=logging.INFO, filename='telegram_bot.log', format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

TELEGRAM_GROUP_ID = int(os.getenv("TELEGRAM_GROUP_ID")) if os.getenv("TELEGRAM_GROUP_ID") else None
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")
TELEGRAM_API_ID = os.getenv("TELEGRAM_API_ID")
TELEGRAM_API_HASH = os.getenv("TELEGRAM_API_HASH")
OBJECTS_PER_PAGE = config("OBJECTS_PER_PAGE", default=6, cast=int)
BASE_URL = config("BASE_URL", default="http://188.121.123.102:8000/")

app = pyrogram.Client("bot", bot_token=TELEGRAM_BOT_TOKEN, api_hash=TELEGRAM_API_HASH, api_id=TELEGRAM_API_ID)

@app.on_message(pyrogram.filters.command("start"))
def handle_notification(client, message):
    message.reply_text("This is a Telegram bot to send notifications for [LLM agent website](http://188.121.123.102:8000/).")

@app.on_message(pyrogram.filters.command("help"))
def handle_help(client, message):
    if message.chat.id != TELEGRAM_GROUP_ID or message.chat.type not in [pyrogram.enums.ChatType.GROUP, pyrogram.enums.ChatType.SUPERGROUP]:
        message.reply_text("This is a Telegram bot to send notifications for [LLM agent website](http://188.121.123.102:8000/).")
    else:
        message.reply_text("This is a Telegram bot to send notifications for [LLM agent website](http://188.121.123.102:8000/). \n/authors to see the authors of this project.\n/emails to see professors ready to send email.")

@app.on_message(pyrogram.filters.command("authors"))
def handle_authors(client, message):
    if message.chat.id != TELEGRAM_GROUP_ID or message.chat.type not in [pyrogram.enums.ChatType.GROUP, pyrogram.enums.ChatType.SUPERGROUP]:
        message.reply_text("Command not allowed here")
    else:
        keyboard, message_text = make_keyboard_and_message_for_authors(0)
        message.reply_text(text=message_text, reply_markup=keyboard)

@app.on_callback_query(pyrogram.filters.regex(r"^authors&") | pyrogram.filters.regex(r"^emails&"))
def handle_callback_query(client, callback_query):
    try:
        if callback_query.message.chat.id != TELEGRAM_GROUP_ID or callback_query.message.chat.type not in [pyrogram.enums.ChatType.GROUP, pyrogram.enums.ChatType.SUPERGROUP]:
            callback_query.answer("Command not allowed here")
            return
        data = callback_query.data
        if not data:
            callback_query.answer()
            return
        context, command = callback_query.data.split("&")
        context_handler_map = {
            "authors": handle_authors_callback,
            "emails": handle_emails_callback,
        }
        callback_handler = context_handler_map.get(context)
        if callback_handler:
            callback_handler(client, callback_query, command)
    except Exception as e:
        callback_query.answer("An error occurred.")

def handle_authors_callback(client, callback_query, command):
    if command.startswith("next") or command.startswith("previous"):
        page_number = int(command.split("_")[1])
        keyboard, message = make_keyboard_and_message_for_authors(page_number)
        callback_query.edit_message_text(text=message, reply_markup=keyboard)
    else:
        author_id, current_page = map(int, command.split("_"))
        keyboard, message = make_keyboard_and_message_for_author(author_id, current_page)
        callback_query.edit_message_text(text=message, reply_markup=keyboard)
    callback_query.answer()

def make_keyboard_and_message_for_authors(page_number):
    authors = Author.objects.filter(openalex_called=True).order_by('name')
    max_pages = (authors.count() + OBJECTS_PER_PAGE - 1) // OBJECTS_PER_PAGE
    if authors.exists():
        message = """Below you can choose authors whose information has been collected by the LLM agent. Choose any author to see more information about them."""
        list_buttons = []
        current_buttons = []
        for author in authors[page_number * OBJECTS_PER_PAGE:(page_number + 1) * OBJECTS_PER_PAGE]:
            current_buttons.append(pyrogram.types.InlineKeyboardButton(author.name, callback_data=f"authors&{author.id}_{page_number}"))
            if len(current_buttons) == 2:
                list_buttons.append(current_buttons)
                current_buttons = []
        if current_buttons:
            current_buttons.append(pyrogram.types.InlineKeyboardButton("-", callback_data=f"-"))
            list_buttons.append(current_buttons)
        if page_number == 0:
            list_buttons.append([pyrogram.types.InlineKeyboardButton("Next", callback_data=f"authors&next_{page_number + 1}")])
        elif page_number < max_pages - 1:
            list_buttons.append([
                pyrogram.types.InlineKeyboardButton("Previous", callback_data=f"authors&previous_{page_number - 1}"),
                pyrogram.types.InlineKeyboardButton("Next", callback_data=f"authors&next_{page_number + 1}")
            ])
        else:
            list_buttons.append([pyrogram.types.InlineKeyboardButton("Previous", callback_data=f"authors&previous_{page_number - 1}")])
        keyboard = pyrogram.types.InlineKeyboardMarkup(list_buttons)
        return keyboard, message
    else:
        message = "No authors found with collected information."
        return None, message

def make_keyboard_and_message_for_author(id, current_page):
    author = Author.objects.get(id=id)
    message = f"""Author: {author.name}
Interests: {author.interests or "Not specified"}
Email: {author.email or "Not specified"}
{('[ORCID URL](' + author.orcid_url + ')') if author.orcid_url else "ORC_ID: Not specified"}
{('[OPELALEX URL](' + author.openalex_url + ')') if author.openalex_url else "OpenAlex URL: Not specified"}"""
    list_buttons = [
        [pyrogram.types.InlineKeyboardButton("Send Email", callback_data=f"emails&{author.id}"),
        pyrogram.types.InlineKeyboardButton("Back to authors", callback_data=f"authors&next_{current_page}")],
    ]
    if not author.email:
        list_buttons.append([pyrogram.types.InlineKeyboardButton("Set Email", url=BASE_URL + f"author/{author.id}/")])
    keyboard = pyrogram.types.InlineKeyboardMarkup(list_buttons)
    return keyboard, message

def handle_emails_callback(client, callback_query, command):
    pass

@app.on_message(pyrogram.filters.command("emails"))
def handle_emails(client, message):
    if message.chat.id != TELEGRAM_GROUP_ID or message.chat.type not in [pyrogram.enums.ChatType.GROUP, pyrogram.enums.ChatType.SUPERGROUP]:
        message.reply_text("Command not allowed here")
    else:
        # todo send message with buttons
        pass

def ensure_telegram_config():
    if not TELEGRAM_API_HASH or not TELEGRAM_BOT_TOKEN or not TELEGRAM_API_ID:
        raise ValueError("Telegram group ID and bot token must be set in environment variables.")

def run_telegram_bot():
    ensure_telegram_config()
    print("Starting Telegram bot...")
    app.run()

def send_telegram_notification(message: str, keyboard=None):
    ensure_telegram_config()
    if TELEGRAM_GROUP_ID is None:
        raise ValueError("Telegram group ID is not set.")
    
    with app:
        app.send_message(chat_id=TELEGRAM_GROUP_ID, text=message, reply_markup=keyboard)