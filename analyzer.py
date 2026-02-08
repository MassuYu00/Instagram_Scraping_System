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
    """
    Analyzes a single post using Gemini 1.5 Pro.
    Expects post_data to be a dictionary with 'text' and 'imageUrl' keys.
    """
    text = post_data.get("text", "")
    image_url = post_data.get("imageUrl", "")
    
    # Prompt construction
    prompt = f"""
    Analyze the following Instagram post content for a portal site "Toronto Info" targeting Japanese people in Toronto.
    
    **Input Data:**
    - Text: {text}
    - Image URL: {image_url} (Please analyze the image content if possible, accessing the URL directly might not be supported in this script without downloading, but treat the text as primary source + OCR if image bytes were provided. *Note: In a production script, we would download the image bytes and pass them to Gemini.*)
    
    **Instructions:**
    1.  **Classify** the post into one of these categories: [Job, House, Event, Ignore].
        -   **Job**: Recruitment, hiring, part-time, full-time.
        -   **House**: Room for rent, apartment, roommate search.
        -   **Event**: Party, meetup, festival, workshop.
        -   **Ignore**: Irrelevant content, spam, or not related to Toronto/Japan/Living.
    2.  **Extract** information based on the category.
    3.  **Rewrite** the description into a polite, modern, and sincere Japanese introduction (max 150 chars) suitable for "Toronto Info".
    
    **Output JSON Schema:**
    ```json
    {{
      "category": "Job | House | Event | Ignore",
      "data": {{
        "instagram_shortcode": "{post_data.get('shortcode', '')}",
        "original_url": "{post_data.get('postUrl')}",
        "posted_at": "{post_data.get('timestamp')}",
        "author": "{post_data.get('username')}",
        "rewritten_text": "Translated/Rewritten description...",
        
        // Fields for Job
        "job_title": "...",
        "job_description_summary": "...", // 100 chars
        "shop_name": "...",
        "location": "...",
        "apply_method": "...",
        
        // Fields for House
        "rent_price": 0, // Number (CAD)
        "area": "...",
        "nearest_station": "...",
        "room_type": "...",
        "move_in_date": "...",
        
        // Fields for Event
        "event_name": "...",
        "event_date": "...",
        "event_place": "..."
      }}
    }}
    ```
    
    Return ONLY the JSON.
    """
    
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
