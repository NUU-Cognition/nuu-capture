#!/usr/bin/env python3
"""
Single-file script to process a PDF from a URL and save outputs.
Includes detailed debugging prints.
"""
import os
import json
import httpx
import base64
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# --- Configuration ---
DOCUMENT_URL = "https://openreview.net/pdf?id=nAFBHoMpQs"
OUTPUT_DIR = Path("document_ocr_test") # Using a new name to avoid conflicts

def save_image_from_data(image_data_uri, page_index, image_index, output_dir):
    """Saves a single base64 encoded image, inferring the type from the data URI."""
    if not image_data_uri:
        print("    ->  FAILED: No image data provided.")
        return False
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        pure_base64_data = image_data_uri
        extension = ".unknown"  # Default extension

        # --- Debug Print ---
        # Print the first 80 characters of the raw data string
        print(f"    -> Raw image_data string (first 80 chars): {image_data_uri[:80]}")

        # Check if the data is a full data URI (e.g., "data:image/jpeg;base64,...")
        if image_data_uri.startswith('data:image/') and ';base64,' in image_data_uri:
            print("    -> Detected data URI prefix. Parsing...")
            prefix, pure_base64_data = image_data_uri.split(',', 1)
            mime_type = prefix.split(';')[0].split(':')[1]
            image_format = mime_type.split('/')[-1]
            if image_format:
                extension = f".{image_format.lower()}"
                print(f"    -> Parsed extension: {extension}")
        else:
            # Fallback to magic number check if no prefix is available
            print("    -> No data URI prefix. Falling back to magic number check...")
            if pure_base64_data.startswith("/9j/"):
                extension = ".jpeg"
            elif pure_base64_data.startswith("iVBOR"):
                extension = ".png"
            elif pure_base64_data.startswith("R0lGOD"):
                extension = ".gif"
            print(f"    -> Inferred extension: {extension}")

        filename = f"page_{page_index + 1}_image_{image_index + 1}{extension}"
        file_path = output_dir / filename

        image_bytes = base64.b64decode(pure_base64_data)
        with open(file_path, "wb") as f:
            f.write(image_bytes)

        print(f"    -> ✅ Successfully saved image: {file_path}")
        return True
    except Exception as e:
        print(f"    -> ❌ FAILED to save image on page {page_index + 1}: {e}")
        return False

def main():
    """Main function to run the OCR pipeline."""
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY environment variable is required")

    print("🚀 Starting PDF Processing with Mistral OCR")
    print("==================================================")
    print(f"📄 Processing document from URL: {DOCUMENT_URL}")

    base_url = "https://api.mistral.ai/v1"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-ocr-latest",
        "document": {"type": "document_url", "document_url": DOCUMENT_URL},
        "include_image_base64": True
    }

    try:
        with httpx.Client() as client:
            response = client.post(f"{base_url}/ocr", headers=headers, json=payload, timeout=600.0)
            if response.status_code != 200:
                raise Exception(f"OCR API error: {response.status_code} - {response.text}")

            result = response.json()
            markdown_content = ""
            images_saved_count = 0

            pages = result.get("pages", [])
            for page_index, page in enumerate(pages):
                if "markdown" in page:
                    markdown_content += page["markdown"] + "\n\n"

                page_images = page.get("images", [])
                print(f"  - Processing Page {page_index + 1}: Found {len(page_images)} image(s) in API response.")

                if page_images:
                    for image_index, img in enumerate(page_images):
                        # --- Debug Print ---
                        print(f"    -> Debugging image {image_index + 1} on page {page_index + 1}:")
                        print(f"    -> API provided 'type' key: {img.get('type')}")
                        
                        image_data_str = img.get("image_base64") or img.get("base64", "")
                        
                        if save_image_from_data(image_data_str, page_index, image_index, OUTPUT_DIR):
                            images_saved_count += 1
            
            # Save the markdown content
            markdown_file_path = OUTPUT_DIR / "document_content.md"
            with open(markdown_file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print("\n✅ Document processing finished!")
            print(f"💾 All outputs saved to: {OUTPUT_DIR.resolve()}")
            print("\n✅ Processing task completed successfully!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()