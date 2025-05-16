from playwright.sync_api import sync_playwright
import re
# from utils.config import config

# CHARACTER_LIMIT = int(config("CHARACTER_LIMIT"))
CHARACTER_LIMIT = 1000

def web_crawler(url: str) -> str:
    """
    This function gets a url and returns the content of the page.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()

        page.goto(url, wait_until="networkidle")
        content = page.content()
        browser.close()
    pattern = r'\b\w*\d+\w*\b'
    content = re.sub(pattern, '', content)
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'\n[ \n]+', '\n', content)
    print(len(content))
    return content[:CHARACTER_LIMIT] 

if __name__ == "__main__":
    # Example usage 
    url = "https://icml.cc/virtual/2024/papers.html?filter=titles"
    content = web_crawler(url)
    print(content)