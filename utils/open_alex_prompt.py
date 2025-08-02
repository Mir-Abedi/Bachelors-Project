from webpages.models import WebPage
from utils import config

SYSTEM_PROMPT = """
You are an AI assistant tasked with processing a fragment of HTML content to identify Persian/Iranian authors and analyze their interests using provided tools. Your goal is to:

1. Parse the HTML fragment to extract meaningful text, ignoring HTML tags and irrelevant markup (e.g., <div>, <span>, <p>).
2. Identify any mentioned authors in the extracted text.
3. Determine if the author is Persian/Iranian based on their name, context, or cultural indicators (e.g., Persian names like 'Mohammad', 'Ali', 'Fatemeh', references to Iran, Persian literature, or cultural elements).
4. If an author is identified as Persian/Iranian, use the `get_author_interests` tool to retrieve their interests.
5. Check if the author's interests include topics related to Large Language Models (LLMs), Natural Language Processing (NLP), or similar fields (e.g., machine learning, artificial intelligence, computational linguistics).
6. If the author's interests include LLMs, NLP, or related fields, use the `save_author` tool to save the author in the database.
7. If no Persian/Iranian author is identified, or if the author's interests do not include LLMs/NLP, do not save the author and proceed to the next task.

Handle the HTML fragment carefully to extract only relevant text. Be precise in identifying Persian/Iranian authors and only call the tools when necessary. If the content does not mention an author or the author is not Persian/Iranian, skip the tool calls and return a message indicating no relevant author was found.
"""

HUMAN_PROMPT = """
Here is a fragment of HTML content to process:

{content}

Please parse the HTML fragment to extract meaningful text and identify any Persian/Iranian authors. If found, use the `get_author_interests` tool to retrieve their interests and check if they include Large Language Models (LLMs), Natural Language Processing (NLP), or related fields. If such interests are present, use the `save_author` tool to save the author in the database. Provide a brief summary of your actions and findings.
"""

class AnalyzePageStartingPrompt:
    def __init__(self, webpage: WebPage):
        self.webpage = webpage
        self.system_prompt = SYSTEM_PROMPT
        self.prompt = HUMAN_PROMPT
        self.max_parts = config("MAX_WEB_PAGE_PARTS", cast=int, default=10)

    def __iter__(self):
        for web_page_part in self.webpage.parts.filter(is_done=False).order_by("part_number").limit(self.max_parts):
            yield [("system", self.system_prompt), ("human", self.prompt.format(content=web_page_part.raw_html))]
            web_page_part.is_done = True
            web_page_part.save()