import json
import time
from scraper import fetch_instagram_posts
from analyzer import analyze_post
from database import save_post

import argparse

# Category priority: Job > House > Event > Ignore
CATEGORY_PRIORITY = {"Job": 0, "House": 1, "Event": 2, "Ignore": 3, "Error": 4}

def main():
    parser = argparse.ArgumentParser(description="Toronto Info Scraper")
    parser.add_argument("--country", type=str, default="Toronto", help="Target country (e.g. Toronto, Thailand)")
    parser.add_argument("--days", type=int, default=14, help="Number of days to filter posts (default: 14)")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of posts to process (default: 10)")
    parser.add_argument("--no-skip-duplicates", action="store_true", help="Disable duplicate filtering")
    args = parser.parse_args()
    
    skip_duplicates = not args.no_skip_duplicates
    
    print(f"=== Starting Content Aggregator for {args.country} ===")
    print(f"Settings: Days={args.days}, Limit={args.limit}, SkipDuplicates={skip_duplicates}")
    
    # 1. Fetch Posts
    print("\n[1/3] Fetching posts from Instagram (Apify)...")
    try:
        posts = fetch_instagram_posts(
            country=args.country,
            days_filter=args.days,
            max_posts=args.limit,
            skip_duplicates=skip_duplicates
        )
        print(f"Found {len(posts)} potential posts.")
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return

    if not posts:
        print("No posts found to process.")
        return

    # 2. Analyze all posts first
    print("\n[2/3] Analyzing posts...")
    analyzed_results = []
    
    for i, post in enumerate(posts):
        print(f"\n--- Analyzing Post {i+1}/{len(posts)} ---")
        try:
            print(f"Analyzing post from {post.get('username')}...")
            analysis_result = analyze_post(post)
            
            category = analysis_result.get("category", "Error")
            print(f"Category: {category}")
            
            if category == "Error":
                print(f"Skipping due to analysis error: {analysis_result.get('error')}")
                continue

            # Preserve metadata from source post
            if "data" not in analysis_result:
                analysis_result["data"] = {}
            
            analysis_result["data"]["instagram_shortcode"] = post.get("shortcode")
            analysis_result["data"]["original_url"] = post.get("postUrl")
            analysis_result["data"]["posted_at"] = post.get("timestamp")
            analysis_result["data"]["author"] = post.get("username")
            
            analyzed_results.append(analysis_result)
            
            # Respect rate limits (Gemini Free Tier is ~15 RPM)
            time.sleep(20)
            
        except Exception as e:
            print(f"Error processing post: {e}")
            continue

    # 3. Sort by category priority (Job > House > Event > Ignore)
    print("\n[3/3] Sorting by priority and saving...")
    analyzed_results.sort(key=lambda x: CATEGORY_PRIORITY.get(x.get("category", "Ignore"), 3))
    
    # Count by category
    category_counts = {}
    for result in analyzed_results:
        cat = result.get("category", "Unknown")
        category_counts[cat] = category_counts.get(cat, 0) + 1
    print(f"Category breakdown: {category_counts}")
    
    # Save sorted results
    saved_count = 0
    for result in analyzed_results:
        if save_post(result):
            print(f"Saved {result.get('category')} post: {result.get('data', {}).get('instagram_shortcode')}")
            saved_count += 1
        else:
            print("Failed to save.")

    # Summary
    print("\n=== Execution Summary ===")
    print(f"Total Fetched: {len(posts)}")
    print(f"Analyzed: {len(analyzed_results)}")
    print(f"Saved to DB: {saved_count}")
    print(f"Priority order: Job({category_counts.get('Job', 0)}) > House({category_counts.get('House', 0)}) > Event({category_counts.get('Event', 0)}) > Ignore({category_counts.get('Ignore', 0)})")
    print("=== Done ===")

if __name__ == "__main__":
    main()

