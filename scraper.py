import os
import requests
import json
from dotenv import load_dotenv
from supabase import create_client

# Load environment variables
load_dotenv()

APIFY_TOKEN = os.getenv("APIFY_TOKEN")

# Supabase for duplicate check
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

def get_existing_shortcodes():
    """Fetch existing shortcodes from DB to avoid duplicate processing."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        return set()
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        result = supabase.table("posts").select("instagram_shortcode").execute()
        return {row["instagram_shortcode"] for row in result.data if row.get("instagram_shortcode")}
    except Exception as e:
        print(f"Warning: Could not fetch existing shortcodes: {e}")
        return set()
APIFY_ACTOR_ID = "shu8hvrXbJbY3Eb9W"  # Instagram Scraper (apify/instagram-scraper) - confirm this ID or similar

COUNTRY_TARGETS = {
    "Toronto": {
        "hashtags": ["torontojobs", "torontorentals", "トロント求人", "torontoevents"],
        "accounts": ["blogto", "torontolife"]
    },
    "Thailand": {
        "hashtags": ["thailandjobs", "bangkokrentals", "タイ就職", "バンコク生活", "thailandtravel"],
        "accounts": [] # Add accounts if known
    },
    "Philippines": {
        "hashtags": ["philippinesjobs", "manilarentals", "セブ島留学", "フィリピン求人", "manilalife"],
        "accounts": []
    },
    "UK": {
        "hashtags": ["ukjobs", "londonrentals", "イギリスワーホリ", "ロンドン生活", "uklife"],
        "accounts": []
    },
    "Australia": {
        "hashtags": ["australiajobs", "sydneyrentals", "オーストラリアワーホリ", "メルボルンカフェ", "sydneylife"],
        "accounts": []
    }
}

def fetch_instagram_posts(custom_targets=None, country="Toronto"):
    """
    Fetches Instagram posts using Apify's Instagram Scraper.
    Refined to use direct URLs for better accuracy and filters by date.
    Accepts custom_targets: list of strings (e.g. "torontojobs", "@blogto").
    Accepts country: string key for COUNTRY_TARGETS (default "Toronto").
    """
    if not APIFY_TOKEN:
        raise ValueError("APIFY_TOKEN not found in environment variables.")

    # Target URLs
    direct_urls = []
    
    if custom_targets:
        print(f"Using custom targets: {custom_targets}")
        for target in custom_targets:
            target = target.strip()
            if target.startswith("@"):
                # Account
                direct_urls.append(f"https://www.instagram.com/{target[1:]}/")
            else:
                # Hashtag (handle # prefix if present)
                tag = target.replace("#", "")
                direct_urls.append(f"https://www.instagram.com/explore/tags/{tag}/")
    else:
        # Default targets based on country
        print(f"Using default targets for country: {country}")
        target_data = COUNTRY_TARGETS.get(country, COUNTRY_TARGETS["Toronto"])
        
        hashtags = target_data.get("hashtags", [])
        accounts = target_data.get("accounts", [])
        
        direct_urls = [f"https://www.instagram.com/explore/tags/{tag}/" for tag in hashtags]
        direct_urls += [f"https://www.instagram.com/{account}/" for account in accounts]

    
    # Configuration for apify/instagram-scraper
    actor_input = {
        "directUrls": direct_urls,
        "resultsType": "posts",
        "resultsLimit": 10, # Increased to 10 as per user request
        "searchType": "hashtag", # Default fallback, though directUrls overrides usually
        "proxy": {
            "useApifyProxy": True
        }
    }
    
    # Run the Actor
    url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs?token={APIFY_TOKEN}"
    
    print(f"Starting Apify Actor ({APIFY_ACTOR_ID})...")
    print(f"Targets: {len(direct_urls)} URLs")
    
    response = requests.post(url, json=actor_input)
    
    if response.status_code != 201:
        print(f"Error starting actor: {response.text}")
        return []
        
    run_data = response.json().get("data")
    run_id = run_data.get("id")
    print(f"Actor run started. ID: {run_id}")
    
    # Wait for run to finish (Polling)
    import time
    while True:
        status_url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs/{run_id}?token={APIFY_TOKEN}"
        status_response = requests.get(status_url)
        status_data = status_response.json().get("data")
        status = status_data.get("status")
        
        print(f"Status: {status}")
        if status in ["SUCCEEDED", "FAILED", "ABORTED"]:
            break
        time.sleep(5)
        
    if status != "SUCCEEDED":
        print("Run failed or was aborted.")
        return []
        
    # Fetch results
    dataset_id = status_data.get("defaultDatasetId")

    dataset_url = f"https://api.apify.com/v2/datasets/{dataset_id}/items?token={APIFY_TOKEN}"
    results_response = requests.get(dataset_url)
    posts = results_response.json()

    formatted_posts = []
    
    # Filtering setup
    from datetime import datetime, timedelta, timezone
    import warnings
    warnings.filterwarnings("ignore", category=FutureWarning)
    
    # Get existing shortcodes to skip duplicates
    existing_shortcodes = get_existing_shortcodes()
    print(f"Found {len(existing_shortcodes)} existing posts in database.")
    
    # Threshold for fresh content (730 days)
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=730)
    
    print(f"Filtering {len(posts)} raw posts...")
    skipped_duplicates = 0
    
    for post in posts:
        # 0. Validate it's a post
        shortcode = post.get("shortCode")
        if not shortcode:
            continue

        # 1. Duplicate Filter - Skip if already in database
        if shortcode in existing_shortcodes:
            skipped_duplicates += 1
            continue

        # 2. Date Filter
        timestamp_str = post.get("timestamp")
        if timestamp_str:
            try:
                post_date = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if post_date < cutoff_date:
                    continue
            except ValueError:
                pass

        text = post.get("caption", "")

        formatted_post = {
            "text": text,
            "imageUrl": post.get("displayUrl") or post.get("thumbnailUrl"),
            "postUrl": f"https://www.instagram.com/p/{shortcode}/",
            "timestamp": timestamp_str,
            "username": post.get("ownerUsername"),
            "shortcode": shortcode
        }
        formatted_posts.append(formatted_post)
    
    # Limit to 10 posts to save API costs
    final_posts = formatted_posts[:10]
    
    print(f"Skipped {skipped_duplicates} duplicate posts.")
    print(f"Retained {len(final_posts)} new posts for processing (Max 10).")
    return final_posts

if __name__ == "__main__":
    results = fetch_instagram_posts()
    print(json.dumps(results, indent=2, ensure_ascii=False))
