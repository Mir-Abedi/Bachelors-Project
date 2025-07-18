from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from langchain_google_genai import ChatGoogleGenerativeAI
from celery import shared_task
import time
import re

from django.utils import timezone
from django.db import transaction

from tools.crawl import web_crawler as web_crawler_tool
from tools.scholar import get_home_page as get_home_page_tool_scholar
from tools.scholar import get_author_interests as get_author_interests_scholar
from tools.open_alex import get_author_interests as get_author_interests_open_alex
from utils.config import config
from utils.open_alex_prompt import AnalyzePageStartingPrompt
from webpages.models import WebPage, WebPagePart, Author

CURRENT_WEB_PAGE = None
MODEL = config("MODEL")
HTML_CUTOFF_CHAR = 5000

@tool
def get_home_page(author_name: str) -> str:
    """
    Get the url of the home page of the author.
    
    This tool could be used to find the personal or academic webpage of an author.
    
    Args:
        author_name (str): name of the author to get home page for.
        
    Returns:
        str: A string containing the author's home page url
    """
    return get_home_page_tool_scholar(author_name)

@tool
def get_author_interests(author_name: str) -> str:
    """
    Get the research interests of the author.
    
    This tool should be used when you need to find the research areas and interests of an academic author.
    
    Args:
        author_name (str): name of the author to get interests for.
        
    Returns:
        str: A string containing the author's research interests
    """
    return get_author_interests_open_alex(author_name)

@tool
def web_crawler(url: str) -> str:
    """
    Returns contents of the webpage given by url.
    This tool could be used to get the content of a webpage.

    Args:
        url (str): URL of the website.

    Returns:
        str: Contents of the website.
    """
    return web_crawler_tool(url)

@tool
def save_author(name: str, interests: str = None, homepage: str = None) -> str:
    """Saves the author along with their interests and their homepage

    Args:
        name (str): author name
        interests (str): author interests | optional
        homepage (str): author homepage | optional
        
    Returns:
        str: Status of the operation
    """
    try:
        Author.objects.create(
            name=name,
            interests=interests,
            homepage=homepage,
            page=CURRENT_WEB_PAGE,
        )
        return "Author saved successfully"
    except Exception as e:
        return "Author not saved"
    


@shared_task
def analyze_web_pages():
    global CURRENT_WEB_PAGE
    while True:
        for webpage in WebPage.objects.filter(parts__is_done=False).iterator(chunk_size=10):
            CURRENT_WEB_PAGE = webpage
            analyze_webpage_for_authors_gemini(webpage)
        time.sleep(10)
    
def analyze_webpage_for_authors(webpage: WebPage):
    starting_prompt = AnalyzePageStartingPrompt(webpage=webpage)

    for prompt in starting_prompt:
        tools = [get_author_interests, save_author]
        tool_node = ToolNode(tools)

        model_with_tools = ChatOllama(model=MODEL).bind_tools(tools)

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

def analyze_webpage_for_authors_gemini(webpage: WebPage):
    starting_prompt = AnalyzePageStartingPrompt(webpage=webpage)

    for prompt in starting_prompt:
        tools = [get_author_interests, save_author]
        tool_node = ToolNode(tools)

        model_with_tools = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash-latest",
            temperature=0.1
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
        end = start + HTML_CUTOFF_CHAR

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


@shared_task
def create_web_page_parts():
    while True:
        for webpage in WebPage.objects.filter(parts__isnull=True).exclude(raw_html="").iterator(chunk_size=10):
            print(f"Creating parts for {webpage.url}")
            with transaction.atomic():
                webpage_parts = get_web_page_parts(webpage)
                WebPagePart.objects.bulk_create(webpage_parts)
        time.sleep(10)

@shared_task
def crawl_web_pages():
    while True:
        for webpage in WebPage.objects.filter(raw_html="").iterator(chunk_size=10):
            print(f"Crawling {webpage.url}")
            webpage.raw_html = web_crawler_tool(webpage.url)
            webpage.crawled_at = timezone.now()
            webpage.save()
        time.sleep(10)

crawl_web_pages.delay()
create_web_page_parts.delay()
analyze_web_pages.delay()