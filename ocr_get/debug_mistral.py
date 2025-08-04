#!/usr/bin/env python3
"""
Step 1: Debug script to call the Mistral OCR API and save the raw JSON response.
"""
import os
import json
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Configuration ---
# The specific URL that is causing issues
DOCUMENT_URL = "https://openreview.net/pdf?id=nAFBHoMpQs"
# The name of the file where the raw API response will be saved
OUTPUT_JSON_FILE = "debug_response.json"

def debug_api_call():
    """Calls the Mistral OCR API and saves the full response to a JSON file."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("❌ Error: MISTRAL_API_KEY environment variable is required.")
        return

    base_url = "https://api.mistral.ai/v1/ocr"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Payload as per official documentation
    payload = {
        "model": "mistral-ocr-latest",
        "document": {
            "type": "document_url",
            "document_url": DOCUMENT_URL
        },
        "include_image_base64": True  # We are explicitly asking for images
    }

    print(f"🔍 Calling Mistral OCR API for URL: {DOCUMENT_URL}")
    print("This may take a moment...")
    
    try:
        with httpx.Client(timeout=600.0) as client:
            response = client.post(base_url, headers=headers, json=payload)
            
            print(f"✅ API call completed with status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Save the full, raw response
                with open(OUTPUT_JSON_FILE, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=4)
                print(f"💾 Full API response saved to: {OUTPUT_JSON_FILE}")
                
                # Analyze the response for images
                print("\n--- Analyzing Response ---")
                pages = result.get("pages", [])
                total_images_found = 0
                if not pages:
                    print("⚠️ Warning: The API response did not contain a 'pages' array.")
                else:
                    for i, page in enumerate(pages):
                        image_count = len(page.get("images", []))
                        if image_count > 0:
                            print(f"    - Page {i+1}: Found {image_count} image(s).")
                            total_images_found += image_count
                        else:
                            print(f"    - Page {i+1}: Found 0 images.")
                
                print("\n" + "="*50)
                if total_images_found > 0:
                    print(f"👍 CONCLUSION: The API *did* return image data.")
                else:
                    print(f"❌ CONCLUSION: The API did NOT return any image data for this document.")
                print("="*50)

            else:
                print(f"❌ API Error: {response.text}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

if __name__ == "__main__":
    debug_api_call()