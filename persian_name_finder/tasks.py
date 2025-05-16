from langchain_ollama import ChatOllama
from langchain_core.tools import tool
from langgraph.graph import StateGraph, MessagesState, START, END
from langgraph.prebuilt import ToolNode
from celery import shared_task

from tools.crawl import web_crawler as wc
from tools.scholar import get_home_page as ghp
from tools.scholar import get_author_interests as gai
from utils.config import config
from utils.starting_prompt import StartingPrompt


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
    return ghp(author_name)

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
    return gai(author_name)

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
    return wc(url)


        
tools = [web_crawler, get_home_page, get_author_interests]
tool_node = ToolNode(tools)

MODEL = config("MODEL")
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

starting_prompt = StartingPrompt()

for prompt in starting_prompt:
    for chunk in app.stream(
        {"messages": prompt}, stream_mode="values"
    ):
        for message in chunk["messages"]:
            if message.content:
                print(message.content)