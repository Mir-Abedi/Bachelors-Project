from dotenv import load_dotenv
import os

def config(key: str) -> str:
    """
    Load specific configuration value from .env file
    
    Args:
        key (str): Configuration key to retrieve
        
    Returns:
        str: Value of the requested configuration key
    """
    load_dotenv()
    return os.getenv(key)


