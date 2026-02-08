import os
import json
import warnings
import requests
# Suppress warnings from google.generativeai and python 3.9 legacy modules
warnings.filterwarnings("ignore", category=FutureWarning)
warnings.filterwarnings("ignore", category=UserWarning)

import google.generativeai as genai
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if not GEMINI_API_KEY:
    raise ValueError("GEMINI_API_KEY not found in environment variables.")

genai.configure(api_key=GEMINI_API_KEY)

# Generation Configuration
generation_config = {
    "temperature": 0.4,
    "top_p": 1,
    "top_k": 32,
    "max_output_tokens": 8192,
}


model = genai.GenerativeModel("gemini-2.0-flash", generation_config=generation_config)


def analyze_post(post_data, use_vision=True):
    """
    Analyzes a single post using Gemini.
    Uses Vision API to analyze images when available, especially for Job posts
    that often contain text in images.
    """
    text = post_data.get("text", "") or ""
    image_url = post_data.get("imageUrl")
    
    prompt = """You are a classifier for Instagram posts. Your job is to find JOB POSTINGS and HOUSING INFO for Japanese expats.

=== CRITICAL RULES ===
1. Job > House > Event > Ignore (priority order)
2. Restaurant food photos = ALWAYS Ignore (even if delicious looking)
3. Restaurant promotions/campaigns = ALWAYS Ignore (NOT Event)
4. Only classify as Event if it's a PUBLIC community event with date/location

=== CATEGORY DEFINITIONS ===

【Job】 ★★★ HIGHEST PRIORITY ★★★
MUST contain hiring/recruitment language:
- Hiring: hiring, 募集, 求人, looking for, we're hiring, 採用, スタッフ募集, 急募
- Employment terms: 正社員, アルバイト, パート, 時給, 給与, salary, $XX/hr, per hour
- Positions: server, cook, chef, kitchen, dishwasher, cashier, staff, barista, ホール, キッチン
- Conditions: full-time, part-time, シフト, 勤務, 経験者優遇, 未経験OK, まかない

【House】 ★★ HIGH PRIORITY ★★
MUST contain rental/housing language:
- Rental: rent, rental, 賃貸, for rent, room available, 入居者募集, 部屋
- Roommate: roommate, ルームメイト, シェアハウス, シェアメイト, housemate
- Price: $/month, 月額, 家賃, utilities, 光熱費込み
- Move-in: move in, 入居, available from, 即入居可

【Event】 ★ LOW PRIORITY - STRICT ★
ONLY for PUBLIC community events:
- MUST have: event name + specific date + public venue
- Examples: Japan Festival 2026, Cherry Blossom Party March 15
- NOT: restaurant specials, menu launches, store openings, happy hours

【Ignore】 ← DEFAULT CATEGORY
Classify as Ignore if NONE of the above match. Especially:
✗ Food photos (料理写真、ラーメン、寿司 etc.)
✗ Restaurant promotions (新メニュー, 期間限定, キャンペーン, 20% off etc.)
✗ Store news without hiring info
✗ Personal posts, travel photos
✗ Generic promotional content
✗ "Come visit us" without hiring

=== OUTPUT FORMAT ===
Return ONLY valid JSON:
{"category":"Job|House|Event|Ignore","data":{"rewritten_text":"Japanese description (max 150 chars)","job_title":"","shop_name":"","location":"","rent_price":0,"area":"","event_name":"","event_date":"","event_place":""}}

Include only relevant fields for the category."""

    content_parts = []
    
    # Try to fetch and include image for vision analysis
    image_included = False
    if use_vision and image_url:
        try:
            print(f"  Fetching image for vision analysis...")
            response = requests.get(image_url, timeout=10)
            if response.status_code == 200 and len(response.content) < 5 * 1024 * 1024:  # Max 5MB
                content_type = response.headers.get('content-type', 'image/jpeg')
                if 'image' in content_type:
                    image_data = response.content
                    content_parts.append({
                        "mime_type": content_type.split(';')[0],
                        "data": image_data
                    })
                    image_included = True
                    print(f"  Image included for analysis ({len(image_data) // 1024}KB)")
        except Exception as e:
            print(f"  Could not fetch image: {e}")
    
    # Add text context
    if text:
        content_parts.append(f"Caption text: {text}\n\n{prompt}")
    else:
        content_parts.append(f"No caption text. Analyze the image only.\n\n{prompt}")
    
    try:
        response = model.generate_content(content_parts)
        result_text = response.text.replace("```json", "").replace("```", "").strip()
        result = json.loads(result_text)
        
        # Log if Job was detected
        if result.get("category") == "Job":
            print(f"  🎯 JOB DETECTED! {result.get('data', {}).get('shop_name', 'Unknown')}")
        
        return result
    except Exception as e:
        print(f"Error analyzing post: {e}")
        return {"category": "Error", "error": str(e)}

if __name__ == "__main__":
    # Test data
    sample_post = {
        "text": "We are hiring! Server position available at KINKA IZAKAYA. Downtown Toronto.",
        "imageUrl": "https://example.com/image.jpg",
        "postUrl": "https://instagram.com/p/xhs8s",
        "timestamp": "2023-10-27T10:00:00",
        "username": "kinka_izakaya"
    }
    
    result = analyze_post(sample_post)
    print(json.dumps(result, indent=2, ensure_ascii=False))

