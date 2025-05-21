from webpages.models import WebPage

SYSTEM_PROMPT = """You are an expert at identifying Iranian authors and researchers.

You have access to these tools:
- get_home_page: Finds an author's homepage URL
- get_author_interests: Gets an author's research interests
- save_author: Save found author

You are given part of a webpage as raw HTML.
DO ALL THESE STEPS IN ORDER:
1. identify any authors with Iranian/Persian names
2. for each Iranian author found:
   - get their homepage with get_home_page
   - get their interests with get_author_interests
3. if the author's interests consist Large Language Models or Natural Language Processing or anything in this context, save the author based on the following rules:
   - In case of no interests found and no homepage found, just save the author with their name, don't use interests or homepage arguments.
   - In case of no homepage found, just save the author with their name and interests, don't use homepage argument.
   - In case of no interests found, just save the author with their name and homepage, don't use interests argument.
IMPORTANT:
DONT ASK ANY QUESTIONS DURING THE PROCESS.
IN CASE OF NO IRANIAN AUTHORS FOUND, SKIP GRACEFULLY.
DONT ASSUME ANYTHING ABOUT AUTHOR INTERESTS OR HOMEPAGE, WAIT FOR THE TOOLS TO RETURN THE RESULTS THEN SAVE BASED ON THE RULES.
IF THE CONTENT IS ONLY SCRIPT OR STYLE, SKIP IT.
"""

USER_PROMPT = """Analyze the following content to retrieve Iranian/Persian authors:

{content}"""

class AnalyzePageStartingPrompt:
    def __init__(self, webpage: WebPage):
        self.webpage = webpage
        self.system_prompt = SYSTEM_PROMPT
        self.prompt = USER_PROMPT

    def __iter__(self):
        for web_page_part in self.webpage.parts.filter(is_done=False).order_by("part_number"):
            yield [("system", self.system_prompt), ("human", self.prompt.format(content=web_page_part.raw_html))]
            web_page_part.is_done = True
            web_page_part.save()
