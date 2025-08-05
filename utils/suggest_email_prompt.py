from webpages.models import Author
from utils import config

SYSTEM_PROMPT = """
You are an AI assistant helping write professional academic invitation emails for the LLM Journal Club.

You MUST:

1. Read the person's name, interests, and work.
2. Generate a relevant and professional email SUBJECT.
3. Generate a warm, respectful, and concise email BODY that invites them to speak at our club.
4. Finally, you MUST call the `save_suggested_email` tool with the subject and body you generated.

Only use the tool after generating a valid subject and body. Do not respond in any other way unless an error occurs.
"""


HUMAN_PROMPT = """
The following person is being considered for an invitation to the LLM Journal Club.

Name: {name}  
Interests: {interests}  
Works: {works}

Please draft:
1. A subject line for the invitation email.
2. A professional and friendly email body inviting them to give a talk.

Once both are ready, **call the `save_suggested_email` tool** to save them.
"""

class SaveEmailPrompt:
    def __init__(self, author: Author):
        self.author = author
        self.system_prompt = SYSTEM_PROMPT
        self.prompt = HUMAN_PROMPT

    def __iter__(self):
        works = [i["title"] for i in self.author.works["results"]] if self.author.works else []
        works = works[:5]
        yield [("system", self.system_prompt), ("human", self.prompt.format(
            name=self.author.name,
            interests=self.author.interests if self.author.interests else "No interests provided",
            works=works,
        ))]