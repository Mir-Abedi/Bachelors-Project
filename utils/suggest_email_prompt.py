from webpages.models import Author
from utils import config

SYSTEM_PROMPT = """You are an expert at writing email. Assisst in writing an email to invite professor and researcher to have a talk in our journal club names LLM Jounal Club.
After generating the suggested body and subject, you should save it in the database using given tools.
"""

HUMAN_PROMPT = """Here is the information about the professor / researcher. assisst in writing an email to invite them to have a talk in our journal club named LLM Journal Club.
name: {name}, {interests}, {works}.
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