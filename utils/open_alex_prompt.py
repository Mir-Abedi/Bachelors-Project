from webpages.models import WebPage
from utils import config

SYSTEM_PROMPT = """
You are an AI assistant helping to write professional invitation emails for the "LLM Journal Club".

Your task is to:

1. Take user-provided information about a professor or researcher (name, interests, and notable work).
2. Use this information to write:
   - A clear, relevant email **subject**.
   - A warm, professional **email body** that invites the person to give a talk at our journal club.
3. Once the subject and body are generated, **you MUST call the `save_suggested_email` tool to store the result**.

The invitation should reflect the guest's academic background and align with the theme of the LLM Journal Club (Large Language Models, NLP, AI, etc.).

Only call the `save_suggested_email` tool **after** generating a valid subject and email body.
"""

HUMAN_PROMPT = """
Please write an invitation email to the following professor or researcher to speak at our LLM Journal Club.

- Name: {name}
- Research Interests: {interests}
- Notable Work / Background: {works}

After writing a suitable subject and email body, make sure to **store it using the `save_suggested_email` tool**.

The email should be warm, professional, and tailored to the person’s expertise.
"""

class AnalyzePageStartingPrompt:
    def __init__(self, webpage: WebPage):
        self.webpage = webpage
        self.system_prompt = SYSTEM_PROMPT
        self.prompt = HUMAN_PROMPT
        self.max_parts = config("MAX_WEB_PAGE_PARTS", cast=int, default=10)

    def __iter__(self):
        for web_page_part in self.webpage.parts.filter(is_done=False).order_by("part_number")[:self.max_parts]:
            yield [("system", self.system_prompt), ("human", self.prompt.format(content=web_page_part.raw_html))]
            web_page_part.is_done = True
            web_page_part.save()