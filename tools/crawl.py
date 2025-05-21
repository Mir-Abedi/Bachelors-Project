from playwright.sync_api import sync_playwright
import re
import time

def web_crawler(url: str) -> str:
    """
    This function gets a url and returns the content of the page.
    """
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True) 
        page = browser.new_page()

        page.goto(url, wait_until="networkidle")
        time.sleep(20)
        content = page.content()
        browser.close()
    pattern = r'\b\w*\d+\w*\b'
    content = re.sub(pattern, '', content)
    content = re.sub(r'[ \t]+', ' ', content)
    content = re.sub(r'\n[ \n]+', '\n', content)
    content = re.sub(r'<(script|style)[^>]*>[\s\S]*?<\/\1>', '', content, flags=re.IGNORECASE)
    return content 

if __name__ == "__main__":
    # Example usage 
    url = "https://icml.cc/virtual/2024/papers.html?filter=titles"
    content = web_crawler(url)
    print(content)