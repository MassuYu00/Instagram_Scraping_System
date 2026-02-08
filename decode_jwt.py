import jwt
import os
from dotenv import load_dotenv
import json

load_dotenv()

key = os.getenv("SUPABASE_KEY")
print(f"Key: {key}")

try:
    # Supabase JWTs aren't encrypted, just signed. We can decode without verifying signature to check payload.
    decoded = jwt.decode(key, options={"verify_signature": False})
    print(json.dumps(decoded, indent=2))
except Exception as e:
    print(f"Error: {e}")
