from webpages.models import Author
from utils import config

SYSTEM_PROMPT = """
You are an expert assistant specialized in drafting professional emails.

Your task is to write a clear and engaging invitation email to a professor or researcher, inviting them to speak at our academic discussion group, the "LLM Journal Club".

After generating the email **subject** and **body**, you must **save the result in the database using the provided tools**.

Always ensure the tone is respectful, enthusiastic, and appropriate for academic correspondence.
"""

HUMAN_PROMPT = """
Please draft an invitation email for the following professor/researcher to speak at our "LLM Journal Club".

Details:
- Name: {name}
- Research Interests: {interests}
- Notable Works or Background: {works}

The output should include:
1. A concise and relevant email **subject**.
2. A warm and professional **email body** inviting them to give a talk.
3. Ensure the email reflects their expertise and aligns with the theme of the LLM Journal Club.

Once the email is generated, please **store it using the available tools**.
"""

class SaveEmailPrompt:
    def __init__(self, author: Author):
        self.author = author
        self.system_prompt = SYSTEM_PROMPT
        self.prompt = HUMAN_PROMPT

    def __iter__(self):
        works = [i["title"] for i in self.author.works["results"]] if self.author.works else []
        yield [("system", self.system_prompt), ("human", self.prompt.format(
            name=self.author.name,
            interests=self.author.interests if self.author.interests else "No interests provided",
            works=works,
        ))]