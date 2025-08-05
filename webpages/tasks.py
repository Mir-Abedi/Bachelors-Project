from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from celery import shared_task
import re
import os
from contextlib import contextmanager

from django.utils import timezone
from django.db import transaction
import requests

from tools.crawl import web_crawler as web_crawler_tool
from tools.scholar import get_home_page as get_home_page_tool_scholar
from tools.scholar import get_author_interests as get_author_interests_scholar
from tools.open_alex import get_author_interests as get_author_interests_open_alex
from tools.open_alex import get_author_dict
from utils.suggest_email_prompt import SaveEmailPrompt
from utils.config import config
from utils.open_alex_prompt import AnalyzePageStartingPrompt
from webpages.models import WebPage, WebPagePart, Author
from pydantic import BaseModel, Field
import redis

from telegram import telegram_sender

CURRENT_WEB_PAGE = None
CURRENT_AUTHOR_EMAIL_SUGGESTION: Author = None

### Get Home Page Tool
class GetHomePageInput(BaseModel):
    author_name: str = Field(..., description="Full Name of the author to get home page for")

@tool(args_schema=GetHomePageInput)
def get_home_page(author_name: str) -> str:
    """
    Get the url of the home page of the author.
    """
    return get_home_page_tool_scholar(author_name)

### Get Author Interests Tool
class GetInterestsInput(BaseModel):
    author_name: str = Field(..., description="Full name of the author to get interests for")

@tool(args_schema=GetInterestsInput)
def get_author_interests(author_name: str) -> str:
    """
    Get the research interests of the author.
    """
    return get_author_interests_open_alex(author_name)


### Web Crawler Tool
class WebCrawlerInput(BaseModel):
    url: str = Field(..., description="URL of the website to be crawled")

@tool(args_schema=WebCrawlerInput)
def web_crawler(url: str) -> str:
    """
    Returns contents of the webpage given by url.
    """
    return web_crawler_tool(url)

### Save Author Tool
class SaveAuthorInput(BaseModel):
    author_name: str = Field(..., description="Full name of the author to be saved")

@tool(args_schema=SaveAuthorInput)
def save_author(author_name: str) -> str:
    """Saves the author in database.
    """
    try:
        Author.objects.create(
            name=author_name,
            interests=None,
            homepage=None,
            page=CURRENT_WEB_PAGE,
        )
        return "Author saved successfully"
    except Exception as e:
        return "Author not saved"
    
@shared_task(time_limit=3600*3)
def analyze_web_pages():
    with redis_lock("analyzing_web_pages", ttl=3600*4):
        global CURRENT_WEB_PAGE
        webpage = WebPage.objects.filter(parts__is_done=False).first()
        if webpage:
            CURRENT_WEB_PAGE = webpage
            analyze_webpage_for_authors(webpage)

def analyze_webpage_for_authors(webpage: WebPage):
    starting_prompt = AnalyzePageStartingPrompt(webpage=webpage)

    for prompt in starting_prompt:
        tools = [get_author_interests, save_author]
        tool_node = ToolNode(tools)

        if config("USE_OLLAMA"):
            model_with_tools = ChatOllama(model=config("OLLAMA_MODEL")).bind_tools(tools)
        elif config("USE_GEMINI"):
            model_with_tools = ChatGoogleGenerativeAI(
                model=config("GEMINI_MODEL"),
                temperature=0.1
            ).bind_tools(tools)
        else:
            # use api calls
            model_with_tools = ChatOpenAI(
                model=config("OPENAI_API_MODEL"),
                openai_api_base=config("OPENAI_API_ENDPOINT"),
                openai_api_key=os.environ["API_KEY"],
                temperature=0.7,
                max_tokens=512,
            ).bind_tools(tools)

        def should_continue(state: MessagesState):
            messages = state["messages"]
            last_message = messages[-1]
            # Check if there are any tool calls in the last message
            if last_message.tool_calls and len(last_message.tool_calls) > 0:
                # Process all tool calls
                return "tools"
            return END


        def call_model(state: MessagesState):
            messages = state["messages"]
            response = model_with_tools.invoke(messages)
            return {"messages": [response]}


        workflow = StateGraph(MessagesState)

        # Define the two nodes we will cycle between
        workflow.add_node("agent", call_model)
        workflow.add_node("tools", tool_node)

        workflow.add_edge(START, "agent")
        workflow.add_conditional_edges("agent", should_continue, ["tools", END])
        workflow.add_edge("tools", "agent")

        app = workflow.compile()

        for chunk in app.stream(
            {"messages": prompt}, stream_mode="values"
        ):
            for message in chunk["messages"]:
                message.pretty_print()

def get_web_page_parts(webpage: WebPage) -> list[WebPagePart]:
    html = webpage.raw_html
    parts = []
    start = 0
    part_number = 1

    while start < len(html):
        end = start + config("HTML_CUTOFF_CHAR", cast=int)

        if end >= len(html):
            end = len(html)
            split_pos = end
        else:
            lt_pos = html.rfind('<', start, end)
            gt_pos = html.rfind('>', start, end)

            if lt_pos == -1 and gt_pos == -1:
                # Fallback: use last whitespace
                match = list(re.finditer(r'\s', html[start:end]))
                if match:
                    split_pos = start + match[-1].start() + 1
                else:
                    split_pos = end  # No space, hard split
            else:
                # Decide based on which tag is closer to end
                if gt_pos > lt_pos:
                    split_pos = gt_pos + 1  # Include '>' in this part
                else:
                    split_pos = lt_pos      # Start next part with '<'
        

        chunk = html[start:split_pos].strip()
        if chunk:
            parts.append(WebPagePart(
                page=webpage,
                part_number=part_number,
                raw_html=chunk
            ))
            part_number += 1

        start = split_pos

    return parts

### Save Author Tool
class SaveSuggestedEmail(BaseModel):
    subject: str = Field(..., description="Subject of the email to be sent")
    body: str = Field(..., description="Body of the email to be sent")

@tool(args_schema=SaveSuggestedEmail)
def save_suggested_email(body: str, subject: str) -> str:
    """Saves the suggested email for the author in database.
    """
    try:
        CURRENT_AUTHOR_EMAIL_SUGGESTION.suggested_email = body
        CURRENT_AUTHOR_EMAIL_SUGGESTION.suggested_email_subject = subject
        CURRENT_AUTHOR_EMAIL_SUGGESTION.save()
    except Exception as e:
        return "Author not saved"

@shared_task(time_limit=3600*3)
def suggest_email_to_authors():
    with redis_lock("suggesting_email_to_authors", ttl=3600*4):
        global CURRENT_AUTHOR_EMAIL_SUGGESTION
        author = Author.objects.filter(suggested_email__isnull=True, email__isnull=False).first()
        if author:
            print(f"Suggesting email for {author.name}")
            CURRENT_AUTHOR_EMAIL_SUGGESTION = author
            save_prompt = SaveEmailPrompt(author=author)

            for prompt in save_prompt:
                tools = [save_suggested_email]
                tool_node = ToolNode(tools)

                if config("USE_OLLAMA"):
                    model_with_tools = ChatOllama(model=config("OLLAMA_MODEL")).bind_tools(tools)
                elif config("USE_GEMINI"):
                    model_with_tools = ChatGoogleGenerativeAI(
                        model=config("GEMINI_MODEL"),
                        temperature=0.1
                    ).bind_tools(tools)
                else:
                    # use api calls
                    model_with_tools = ChatOpenAI(
                        model=config("OPENAI_API_MODEL"),
                        openai_api_base=config("OPENAI_API_ENDPOINT"),
                        openai_api_key=os.environ["API_KEY"],
                        temperature=0.7,
                        max_tokens=512,
                    ).bind_tools(tools)

                def should_continue(state: MessagesState):
                    messages = state["messages"]
                    last_message = messages[-1]
                    # Check if there are any tool calls in the last message
                    if last_message.tool_calls and len(last_message.tool_calls) > 0:
                        # Process all tool calls
                        return "tools"
                    return END


                def call_model(state: MessagesState):
                    messages = state["messages"]
                    response = model_with_tools.invoke(messages)
                    return {"messages": [response]}


                workflow = StateGraph(MessagesState)

                # Define the two nodes we will cycle between
                workflow.add_node("agent", call_model)
                workflow.add_node("tools", tool_node)

                workflow.add_edge(START, "agent")
                workflow.add_conditional_edges("agent", should_continue, ["tools", END])
                workflow.add_edge("tools", "agent")

                app = workflow.compile()

                for chunk in app.stream(
                    {"messages": prompt}, stream_mode="values"
                ):
                    for message in chunk["messages"]:
                        message.pretty_print()

@shared_task(time_limit=3600*3)
def create_web_page_parts():
    with redis_lock("creating_web_page_parts", ttl=3600*4):
        webpage = WebPage.objects.filter(parts__isnull=True).exclude(raw_html="").first()
        if webpage:
            print(f"Creating parts for {webpage.url}")
            with transaction.atomic():
                webpage_parts = get_web_page_parts(webpage)
                WebPagePart.objects.bulk_create(webpage_parts)

@shared_task(time_limit=3600*3)
def crawl_web_pages():
    with redis_lock("crawling_web_pages", ttl=3600*4):
        webpage = WebPage.objects.filter(raw_html="").first()
        if webpage:
            print(f"Crawling {webpage.url}")
            webpage.raw_html = web_crawler_tool(webpage.url)
            webpage.crawled_at = timezone.now()
            webpage.save()

@contextmanager
def redis_lock(key, ttl=3600*4):
    redis_client = redis.Redis(host='localhost', port=6379, db=0)
    if redis_client.set(key, "locked", ex=ttl, nx=True):
        try:
            yield
        finally:
            redis_client.delete(key)
    else:
        yield

@shared_task(time_limit=3600*3)
def fill_open_alex_data():
    with redis_lock("filling_open_alex_data", ttl=3600*4):
        author = Author.objects.filter(openalex_called=False).first()
        if author:
            try:
                d = get_author_dict(author.name)
                author.orcid_url = d.get("ids", {}).get("orcid", "")
                author.openalex_url = d.get("ids", {}).get("openalex", "")
                if d.get("works_api_url"):  
                    author.works = requests.get(d.get("works_api_url")).json()
                author.openalex_called = True
                author.interests = get_author_interests_open_alex(author.name)
                author.save()
            except Exception as e:
                print(f"Error filling OpenAlex data for {author.name}: {e}")
                author.openalex_retries += 1
                if author.openalex_retries >= 5:
                    author.openalex_called = True
                author.save()

@shared_task(time_limit=3600*3)
def notify_new_authors():
    with redis_lock("notifying_new_authors", ttl=3600*4):
        new_authors = Author.objects.filter(notified_found=False, interests__isnull=False)
        base_url = config("BASE_URL", default="http://localhost:8000/")
        if new_authors.count() == 1:
            message = f"New author found: [{new_authors.first().name}]({base_url}/author/{new_authors.first().id}), set their email to send them an invitation."
        if new_authors.count() == 2:
            message = f"New authors found: [{new_authors.first().name}]({base_url}/author/{new_authors.first().id}) and [{new_authors.last().name}]({base_url}/author/{new_authors.last().id}), set their emails to send them invitations."
        if new_authors.count() > 2:
            message = f"{new_authors.count()} new authors were found. [Set their emails]({base_url}/authors) to send them invitations."
        else:
            return
        telegram_sender.send_telegram_notification(message=message)
        new_authors.update(notified_found=True)

@shared_task(time_limit=3600*3)
def notify_sending_email():
    with redis_lock("notifying_sending_email", ttl=3600*4):
        new_authors = Author.objects.filter(notified_email=False, suggested_email__isnull=False)
        base_url = config("BASE_URL", default="http://localhost:8000/")
        if new_authors.count() == 1:
            message = f"Suggested email for author [{new_authors.first().name}]({base_url}/author/{new_authors.first().id}) is ready, send them their [email]({new_authors.first().name}]({base_url}/author/{new_authors.first().id}/send-email/)."
        if new_authors.count() == 2:
            message = f"Suggested email for authors [{new_authors.first().name}]({base_url}/author/{new_authors.first().id}) and [{new_authors.last().name}]({base_url}/author/{new_authors.last().id}) is ready, send them their [emails]({base_url}/authors)."
        if new_authors.count() > 2:
            message = f"Suggested emails for {new_authors.count()} authors are ready. [Send their emails]({base_url}/authors)."
        else:
            return
        telegram_sender.send_telegram_notification(message=message)
        new_authors.update(notified_email=True)

