from analyzer import analyze_post
import json

# Sample data mimicking a scraped Instagram post
sample_post = {
    "text": "We are looking for a new server! Join our team at Kinka Izakaya. Email resume to hr@kinka.com. #torontojobs",
    "imageUrl": "https://example.com/image.jpg",
    "postUrl": "https://instagram.com/p/test12345",
    "timestamp": "2024-02-07T12:00:00",
    "username": "kinka_izakaya"
}

print("Testing analyzer with sample post...")
try:
    result = analyze_post(sample_post)
    print("Analysis Result:")
    print(json.dumps(result, indent=2, ensure_ascii=False))
    
    if result.get("category") and result.get("category") != "Error":
        print("\nSUCCESS: Analyzer returned a valid category.")
    else:
        print("\nFAILURE: Analyzer returned an error or invalid format.")
        
except Exception as e:
    print(f"\nCRITICAL FAILURE: {e}")
