import json
import time
from scraper import fetch_instagram_posts
from analyzer import analyze_post
from database import save_post

import argparse

def main():
    parser = argparse.ArgumentParser(description="Toronto Info Scraper")
    parser.add_argument("--targets", type=str, help="Comma-separated list of targets (e.g. '#job,@blogto')")
    parser.add_argument("--country", type=str, default="Toronto", help="Target country (e.g. Toronto, Thailand)")
    args = parser.parse_args()
    
    custom_targets = None
    if args.targets:
        custom_targets = args.targets.split(",")
    
    print(f"=== Starting Content Aggregator for {args.country} ===")
    
    # 1. Fetch Posts
    print("\n[1/3] Fetching posts from Instagram (Apify)...")
    try:
        posts = fetch_instagram_posts(custom_targets=custom_targets, country=args.country)
        print(f"Found {len(posts)} potential posts.")
    except Exception as e:
        print(f"Error fetching posts: {e}")
        return

    if not posts:
        print("No posts found to process.")
        return

    # 2. Analyze & Save
    print("\n[2/3] Analyzing and Saving posts...")
    processed_count = 0
    saved_count = 0
    
    for i, post in enumerate(posts):
        print(f"\n--- Processing Post {i+1}/{len(posts)} ---")
        try:
            # Analyze
            print(f"Analyzing post from {post.get('username')}...")
            analysis_result = analyze_post(post)
            
            category = analysis_result.get("category")
            print(f"Category: {category}")
            
            if category == "Error":
                print(f"Skipping due to analysis error: {analysis_result.get('error')}")
                continue

            # CRITICAL FIX: Ensure metadata (shortcode, url) is preserved.
            # Gemini might lose them or return null. We force them from the source post.
            if "data" not in analysis_result:
                analysis_result["data"] = {}
            
            analysis_result["data"]["instagram_shortcode"] = post.get("shortcode")
            # Only set if missing or empty, or just overwrite to be safe? Overwrite is safest.
            analysis_result["data"]["original_url"] = post.get("postUrl")
            analysis_result["data"]["posted_at"] = post.get("timestamp")
            analysis_result["data"]["author"] = post.get("username")
                
            # Save
            if save_post(analysis_result):
                print("Successfully saved to database.")
                saved_count += 1
            else:
                print("Failed to save or skipped.")
            
            processed_count += 1
            # Respect rate limits (Gemini Free Tier is ~15 RPM, so waiting 20s is safe)
            time.sleep(20) 
            
        except Exception as e:
            print(f"Error processing post: {e}")
            continue

    # 3. Summary
    print("\n=== Execution Summary ===")
    print(f"Total Fetched: {len(posts)}")
    print(f"Processed: {processed_count}")
    print(f"Saved to DB: {saved_count}")
    print("=== Done ===")

if __name__ == "__main__":
    main()
