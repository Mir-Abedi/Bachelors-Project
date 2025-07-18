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
    if os.getenv(key) is None:
        raise KeyError(f"Configuration key '{key}' not found in .env file.")
    if os.getenv(key).lower() in ["false", "true", "1", "0"]:
        return os.getenv(key).lower() == "true" or os.getenv(key) == "1"
    return os.getenv(key)


