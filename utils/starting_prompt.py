from persian_name_finder.models import WebPage

SYSTEM_PROMPT = """You are an expert at identifying Iranian authors and researchers.

You have access to these tools:
- web_crawler: Gets the contents of a webpage given its URL
- get_home_page: Finds an author's homepage URL
- get_author_interests: Gets an author's research interests
- save_author: Save found author

do all the steps in the following order:
1. use web_crawler to get the webpage contents
2. identify any authors with Iranian/Persian names
3. for each Iranian author found:
   - get their homepage with get_home_page
   - get their interests with get_author_interests
finally, if the author's interests consist Large Language Models or Natural Language Processing or anything in this context, save the author.
"""

USER_PROMPT = """Analyze {URL} to retrieve Iranian/Persian authors"""

class StartingPrompt:
    def __init__(self):
        self.urls = [
            # "https://icml.cc/virtual/2024/papers.html?filter=titles",
            "https://mir-abedi.github.io/names.html",
        ]
        self.system_prompt = SYSTEM_PROMPT
        self.prompt = USER_PROMPT

    def __iter__(self):
        for url in self.urls:
            yield [("system", self.system_prompt), ("human", self.prompt.format(URL=url))]