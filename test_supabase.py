from supabase import create_client
import os
from dotenv import load_dotenv
import json

load_dotenv()

url = os.getenv("SUPABASE_URL")
key = os.getenv("SUPABASE_KEY")

print(f"URL: {url}")
print(f"Key: {key[:10]}...") 

try:
    supabase = create_client(url, key)
    
    print("Attempting to select from 'posts'...")
    response = supabase.table("posts").select("*").limit(1).execute()
    
    print("Success!")
    print(json.dumps(response.data, indent=2))
except Exception as e:
    print(f"Error: {e}")
