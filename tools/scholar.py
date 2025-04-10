from scholarly import scholarly

def get_home_page(author_name: str) -> str:
    """
    Get the url of the home page of the author"""
    search_query = scholarly.search_author(author_name)
    author = next(search_query, None)
    if author:
        author = scholarly.fill(author)
        return author['homepage']
    else:
        return "No URL found for author"

def get_author_interests(author_name: str) -> str:
    """
    Get the research interests of the author"""
    search_query = scholarly.search_author(author_name)
    author = next(search_query, None)
    if author:
        author = scholarly.fill(author)
        return ", ".join(author['interests'])
    else:
        return "No interests found for author"

if __name__ == "__main__":
    # Example usage
    author_name = "Mahdi Jafari Siavoshani"
    print(get_home_page(author_name))
    print(get_author_interests(author_name))