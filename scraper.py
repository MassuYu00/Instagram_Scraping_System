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
APIFY_ACTOR_ID = "apify~instagram-hashtag-scraper"  # Official Apify Instagram Scraper

# =====================================
# 求人/住居情報に特化したターゲット設定
# 
# 重要: レストランアカウントは求人より料理写真が多いため削除
# ハッシュタグ検索を中心に多様なソースから情報を取得
# =====================================
COUNTRY_TARGETS = {
    "Toronto": {
        # ハッシュタグ検索を中心に（多様なソースから取得）
        "hashtags": [
            # 求人系（最優先）
            "torontojobs",           # 求人全般
            "torontohiring",         # 採用情報
            "gtajobs",               # GTA地域求人
            "torontowork",           # 仕事情報
            "hiringtoronto",         # 採用中
            "トロント求人",           # 日本語求人
            "トロント仕事",           # 日本語仕事
            "カナダ求人",             # カナダ全般求人
            "ワーホリ求人",           # ワーホリ向け求人
            # 住居系
            "torontorentals",        # 賃貸全般
            "torontohousing",        # 住居情報
            "torontoroommate",       # ルームメイト
            "トロント賃貸",           # 日本語賃貸
            "トロントシェアハウス",   # シェアハウス
            "トロント部屋探し",       # 部屋探し
        ],
        # 掲示板・コミュニティ系アカウントのみ（レストランは除外）
        "accounts": [
            # 日系コミュニティ掲示板
            "jpcanada_com",          # JPCanada（求人・住居掲示板）
            "eマップル",              # e-Maple（コミュニティ情報）
        ]
    },
    "Thailand": {
        "hashtags": [
            # 求人系
            "bangkokjobs",           # バンコク求人
            "thailandjobs",          # タイ求人
            "タイ求人",               # 日本語求人
            "タイ就職",               # 就職情報
            "バンコク求人",           # バンコク求人
            "タイ転職",               # 転職情報
            "タイ駐在",               # 駐在情報
            # 住居系
            "bangkokrentals",        # バンコク賃貸
            "bangkokcondo",          # コンドミニアム
            "バンコク賃貸",           # 日本語賃貸
            "バンコクコンドミニアム", # コンドミニアム
            "タイ不動産",             # 不動産情報
        ],
        # 不動産・人材紹介会社のみ
        "accounts": [
            "personnelconsultant",   # 人材紹介会社
            "reeracoen_thailand",    # リーラコーエン（人材）
        ]
    },
    "Philippines": {
        "hashtags": [
            # 求人系
            "フィリピン求人",         # 日本語求人
            "セブ求人",               # セブ求人
            "マニラ求人",             # マニラ求人
            "cebujobs",              # セブ求人
            "manilajobs",            # マニラ求人
            "philippinesjobs",       # フィリピン求人
            "フィリピン就職",         # 就職情報
            # 住居系
            "ceburentals",           # セブ賃貸
            "manilarentals",         # マニラ賃貸
            "セブ賃貸",               # セブ賃貸
        ],
        "accounts": [
            "reeracoen_ph",          # 日系人材紹介
        ]
    },
    "UK": {
        "hashtags": [
            # 求人系
            "londonjobs",            # ロンドン求人
            "ukhiring",              # UK採用
            "londonhiring",          # ロンドン採用
            "ukjobs",                # UK求人
            "ロンドン求人",           # 日本語求人
            "イギリス求人",           # イギリス求人
            "イギリスワーホリ求人",   # ワーホリ求人
            "ロンドン仕事",           # 仕事情報
            # 住居系
            "londonrentals",         # ロンドン賃貸
            "londonroomshare",       # ルームシェア
            "londonflat",            # フラット
            "ロンドン賃貸",           # 日本語賃貸
            "ロンドンシェアハウス",   # シェアハウス
        ],
        "accounts": [
            "mixb_london",           # MixB（求人・住居掲示板）
        ]
    },
    "Australia": {
        "hashtags": [
            # 求人系
            "sydneyjobs",            # シドニー求人
            "melbournejobs",         # メルボルン求人
            "australiajobs",         # オーストラリア求人
            "オーストラリア求人",     # 日本語求人
            "シドニー求人",           # シドニー求人
            "メルボルン求人",         # メルボルン求人
            "ワーホリオーストラリア", # ワーホリ情報
            "オーストラリアワーホリ求人", # ワーホリ求人
            # 住居系
            "sydneyrentals",         # シドニー賃貸
            "melbournerentals",      # メルボルン賃貸
            "シドニー賃貸",           # シドニー賃貸
            "メルボルン賃貸",         # メルボルン賃貸
            "シドニーシェアハウス",   # シェアハウス
        ],
        # コミュニティメディアのみ
        "accounts": [
            "nichigopress",          # 日豪プレス（求人掲載多い）
            "jams_tv_au",            # JAMS.TV（求人掲載）
        ]
    }
}

def fetch_instagram_posts(country="Toronto", days_filter=14, max_posts=10, skip_duplicates=True):
    """
    Fetches Instagram posts using Apify's Instagram Scraper.
    Refined to use direct URLs for better accuracy and filters by date.
    
    Args:
        country: string key for COUNTRY_TARGETS (default "Toronto")
        days_filter: number of days to look back (default 14)
        max_posts: maximum number of posts to return (default 10)
        skip_duplicates: whether to skip posts already in database (default True)
    """
    if not APIFY_TOKEN:
        raise ValueError("APIFY_TOKEN not found in environment variables.")

    # Target URLs based on country
    print(f"Using default targets for country: {country}")
    target_data = COUNTRY_TARGETS.get(country, COUNTRY_TARGETS["Toronto"])
    
    hashtags = target_data.get("hashtags", [])
    accounts = target_data.get("accounts", [])
    
    # Configuration for apify/instagram-hashtag-scraper
    # Reference: https://apify.com/apify/instagram-hashtag-scraper
    actor_input = {
        "hashtags": hashtags[:5],  # Use first 5 hashtags to avoid overload
        "resultsLimit": 50,        # Posts per hashtag
        "proxy": {
            "useApifyProxy": True,
            "apifyProxyGroups": ["RESIDENTIAL"]
        }
    }
    
    # Run the Actor
    url = f"https://api.apify.com/v2/acts/{APIFY_ACTOR_ID}/runs?token={APIFY_TOKEN}"
    
    print(f"Starting Apify Actor ({APIFY_ACTOR_ID})...")
    print(f"Hashtags: {actor_input.get('hashtags')}")
    
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
    existing_shortcodes = get_existing_shortcodes() if skip_duplicates else set()
    if skip_duplicates:
        print(f"Found {len(existing_shortcodes)} existing posts in database.")
    else:
        print("Duplicate filtering disabled.")
    
    # Date filter based on days_filter parameter
    cutoff_date = datetime.now(timezone.utc) - timedelta(days=days_filter)
    print(f"Filtering posts newer than: {cutoff_date.strftime('%Y-%m-%d')} ({days_filter} days)")
    
    print(f"Filtering {len(posts)} raw posts...")
    
    skipped_duplicates = 0
    skipped_old = 0
    
    for post in posts:
        # 0. Validate it's a post
        shortcode = post.get("shortCode")
        if not shortcode:
            continue

        # 1. Duplicate Filter - Skip if already in database (only if enabled)
        if skip_duplicates and shortcode in existing_shortcodes:
            skipped_duplicates += 1
            continue

        # 2. Date Filter - Skip posts older than 7 days
        timestamp_str = post.get("timestamp")
        if timestamp_str:
            try:
                post_date = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))
                if post_date < cutoff_date:
                    skipped_old += 1
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
    
    # Limit to max_posts to save API costs
    final_posts = formatted_posts[:max_posts]
    
    print(f"Skipped {skipped_duplicates} duplicate posts.")
    print(f"Skipped {skipped_old} old posts (older than {days_filter} days).")
    print(f"Retained {len(final_posts)} new posts for processing (Max {max_posts}).")
    return final_posts

if __name__ == "__main__":
    results = fetch_instagram_posts()
    print(json.dumps(results, indent=2, ensure_ascii=False))
