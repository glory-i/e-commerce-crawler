"""
Generate secure API keys
"""
import secrets


def generate_api_key(prefix: str = "key") -> str:
    """Generate a secure API key"""
    random_part = secrets.token_urlsafe(32)
    return f"{prefix}_{random_part}"


if __name__ == "__main__":
    print("ADD Generated API Keys to .env:\n")
    
    for i in range(3):
        key = generate_api_key()
        print(f"Key {i+1}: {key}")
    
    key1 = generate_api_key()
    key2 = generate_api_key()
    print(f"API_KEYS={key1},{key2}")