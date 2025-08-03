from scholarly import scholarly, ProxyGenerator
from functools import cache

def get_home_page(author_name: str) -> str:
    """
    Get the url of the home page of the author"""
    author = get_author_dict(author_name)
    if author and "homepage" in author:
        author = scholarly.fill(author)
        return author["homepage"]
    else:
        return "No URL found for author"

def get_author_interests(author_name: str) -> str:
    """
    Get the research interests of the author"""
    author = get_author_dict(author_name)
    if author and "interests" in author:
        author = scholarly.fill(author)
        return ", ".join(author["interests"])
    else:
        return "No interests found for author"

@cache
def get_author_dict(author_name: str):
    """
    Get the author dictionary from scholarly"""
    pg = ProxyGenerator()
    success = pg.ScraperAPI(API_KEY="391cac7f24f5d013fc34880390c43804")
    print(success)
    scholarly.use_proxy(pg)
    search_query = scholarly.search_author(author_name)
    author = next(search_query, None)
    if author:
        return scholarly.fill(author)
    else:
        return {}

if __name__ == "__main__":
    # Example usage
    author_name = "Keivan Rezaei"
    print(get_home_page(author_name))
    print(get_author_interests(author_name))