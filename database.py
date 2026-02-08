import os
import json
from supabase import create_client, Client
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    # We allow import even if envs are missing to avoid crash on load, 
    # but init will fail if called.
    print("Warning: SUPABASE_URL or SUPABASE_KEY not found.")
    supabase: Client = None
else:
    supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

def save_post(analyzed_data):
    """
    Saves the analyzed post data to the Supabase 'posts' table.
    Handles deduplication via 'instagram_shortcode'.
    """
    if not supabase:
        print("Supabase client not initialized.")
        return False

    category = analyzed_data.get("category")
    if category == "Ignore":
        print(f"Skipping ignored post.")
        return True

    data = analyzed_data.get("data", {})
    original_url = data.get("original_url")
    
    # Extract shortcode
    shortcode = data.get("instagram_shortcode")
    
    # Fallback to URL parsing if not provided
    if not shortcode and original_url and "instagram.com/p/" in original_url:
        try:
            shortcode = original_url.split("/p/")[1].split("/")[0]
        except IndexError:
            pass
    
    if not shortcode:
        print(f"Could not extract shortcode. URL: {original_url}")
        return False

    # Prepare payload
    # Mapping analyzed fields to DB columns.
    # We assume the table has columns for common fields and a jsonb 'details' column, 
    # or specific columns. For this implementation, I will map to a generic schema + jsonb.
    
    payload = {
        "instagram_shortcode": shortcode,
        "status": "pending",
        "category": category,
        "original_url": original_url,
        "posted_at": data.get("posted_at"),
        "author": data.get("author"),
        "content": data.get("rewritten_text"), # The rewritten body
        # Store specific fields in a JSONB column 'metadata' or 'details'
        "details": data 
    }

    try:
        # Upsert: Update if exists, Insert if new.
        # on_conflict="instagram_shortcode" is standard for upsert, 
        # but supabase-py uses .upsert() which handles this if 'instagram_shortcode' is PK or unique.
        
        # Check if exists to decide whether to update status or keep 'pending' 
        # (Usually we don't want to revert status if it was published, but requirement says "Update or Skip")
        # "Target: duplicate check (instagram_shortcode) -> Update or Skip"
        # Let's try to select first.
        
        existing = supabase.table("posts").select("id, status").eq("instagram_shortcode", shortcode).execute()
        
        if existing.data:
            print(f"Post {shortcode} already exists. Updating details but keeping status...")
            # We update details but preserve status if it exists? 
            # Or just update everything? User said "Update or Skip".
            # Let's update the content/details in case parsing improved, but keep existing status.
            payload.pop("status") 
            supabase.table("posts").update(payload).eq("instagram_shortcode", shortcode).execute()
        else:
            print(f"Inserting new post {shortcode}...")
            supabase.table("posts").insert(payload).execute()
            
        return True

    except Exception as e:
        print(f"Error saving to Supabase: {e}")
        return False

if __name__ == "__main__":
    # Test stub
    test_data = {
        "category": "Job",
        "data": {
            "original_url": "https://www.instagram.com/p/test_shortcode/",
            "posted_at": "2023-10-27T10:00:00",
            "author": "test_user",
            "rewritten_text": "Looking for a chef...",
            "job_title": "Chef",
            "location": "Toronto"
        }
    }
    save_post(test_data)
