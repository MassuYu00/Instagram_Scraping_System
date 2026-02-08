import os
import json
import warnings
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


model = genai.GenerativeModel("gemini-flash-latest", generation_config=generation_config)


def analyze_post(post_data):
    """Analyzes a single post using Gemini."""
    text = post_data.get("text", "")
    
    prompt = f"""Classify this Instagram post and extract info for Japanese expats.

Text: {text}

Categories: Job(hiring/recruitment), House(rent/roommate), Event(meetup/party), Ignore(spam/irrelevant)

Output JSON only:
{{"category":"Job|House|Event|Ignore","data":{{"rewritten_text":"Japanese description (max 150 chars)","job_title":"","shop_name":"","location":"","rent_price":0,"area":"","event_name":"","event_date":"","event_place":""}}}}

Include only relevant fields for the category. Return ONLY valid JSON."""
    
    # In a real implementation effectively using Multimodal, we would fetch the image bytes:
    # import requests
    # image_bytes = requests.get(image_url).content
    # contents = [prompt, {"mime_type": "image/jpeg", "data": image_bytes}]
    
    # For this skeleton, we assume text-based + URL context (or user implements image fetching)
    # Sending simple text prompt for now.
    
    try:
        response = model.generate_content(prompt)
        return json.loads(response.text.replace("```json", "").replace("```", ""))
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
