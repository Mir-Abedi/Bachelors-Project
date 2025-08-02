from dotenv import load_dotenv
import os

def config(key: str, cast=str, default=None) -> any:
    """
    Load specific configuration value from .env file with type casting and default value
    
    Args:
        key (str): Configuration key to retrieve
        cast (type): Type to cast the value to (default: str)
        default: Default value if key not found (default: None)
        
    Returns:
        any: Value of the requested configuration key cast to specified type
    """
    load_dotenv()
    value = os.getenv(key)
    
    if value is None:
        if default is not None:
            return default
        raise KeyError(f"Configuration key '{key}' not found in .env file.")
        
    try:
        if value.lower() in ["false", "true"]:
            return value.lower() == "true"
        return cast(value)
    except ValueError:
        raise ValueError(f"Cannot cast value '{value}' to {cast.__name__}")

