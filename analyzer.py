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
    
    prompt = """Classify this Instagram post and extract info for Japanese expats.

IMPORTANT: Job postings are HIGH PRIORITY. Look carefully for:
- Hiring/recruitment keywords (hiring, 募集, 求人, looking for staff)
- Job titles (server, cook, chef, staff)
- Restaurant/shop names

Categories:
- Job: hiring, recruitment, job posting, 求人, 募集
- House: rent, roommate, 賃貸, ルームシェア
- Event: meetup, party, イベント
- Ignore: spam, irrelevant, promotional only

Output JSON only:
{"category":"Job|House|Event|Ignore","data":{"rewritten_text":"Japanese description (max 150 chars)","job_title":"","shop_name":"","location":"","rent_price":0,"area":"","event_name":"","event_date":"","event_place":""}}

Include only relevant fields for the category. Return ONLY valid JSON."""

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

