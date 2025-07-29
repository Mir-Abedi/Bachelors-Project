import pyalex
from pyalex import Authors
from time import sleep


MAX_INTERESTS_COUNT = 5

def get_author_interests(author_name: str) -> str:
    """
    Get the research interests of the author"""
    try:
        author = get_author_dict(author_name)
        author_interests = set()
        for topic in author["topics"]:
            if not topic.get("display_name") or topic["display_name"] in author_interests:
                continue
            author_interests.add(topic["display_name"])
            if len(author_interests) >= MAX_INTERESTS_COUNT:
                break
        sleep(1)  # To avoid hitting the API rate limit
        return ", ".join(author_interests)
        
    except Exception as e:
        print(f"Error retrieving interests: {str(e)}")
        return "No interests found for author"

def get_author_dict(author_name: str):
    pyalex.config.email = "amirhoseinabedi80@gmail.com" #todo: round robin for max usage
    return Authors().search_filter(display_name=author_name).get()[0]

if __name__ == "__main__":
    # Example usage
    author_name = "Andrew NG"
    print(get_author_interests(author_name))
