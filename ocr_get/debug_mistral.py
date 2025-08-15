#!/usr/bin/env python3
"""
Debug script to call the Mistral OCR API and save the raw JSON response.
Supports both URL and local file processing.
"""
import os
import json
import httpx
import base64
import argparse
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# --- Default Configuration ---
DEFAULT_DOCUMENT_URL = "https://openreview.net/pdf?id=nAFBHoMpQs"
DEFAULT_OUTPUT_JSON_FILE = "debug_response.json"

def encode_pdf_to_base64(pdf_path):
    """Encode a local PDF file to base64 for API upload."""
    try:
        with open(pdf_path, "rb") as pdf_file:
            return base64.b64encode(pdf_file.read()).decode('utf-8')
    except FileNotFoundError:
        raise FileNotFoundError(f"PDF file not found: {pdf_path}")
    except Exception as e:
        raise Exception(f"Error encoding PDF: {e}")

def is_url(string):
    """Check if a string is a valid URL."""
    try:
        result = urlparse(string)
        return all([result.scheme, result.netloc])
    except:
        return False

def prepare_document_payload(document_input):
    """Prepare the document payload based on input type (URL or local file)."""
    if is_url(document_input):
        print(f"Calling Mistral OCR API for URL: {document_input}")
        return {
            "type": "document_url",
            "document_url": document_input
        }
    else:
        # Treat as local file path
        pdf_path = Path(document_input)
        if not pdf_path.exists():
            raise FileNotFoundError(f"Local PDF file not found: {document_input}")
        if not pdf_path.suffix.lower() == '.pdf':
            raise ValueError(f"File must be a PDF. Got: {pdf_path.suffix}")
            
        print(f"Calling Mistral OCR API for local PDF: {document_input}")
        base64_pdf = encode_pdf_to_base64(pdf_path)
        return {
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{base64_pdf}"
        }

def debug_api_call(document_input, output_json_file):
    """Calls the Mistral OCR API and saves the full response to a JSON file."""
    
    api_key = os.getenv("MISTRAL_API_KEY")
    if not api_key:
        print("- Error: MISTRAL_API_KEY environment variable is required.")
        return

    try:
        document_payload = prepare_document_payload(document_input)
    except Exception as e:
        print(f"- Error preparing document: {e}")
        return

    base_url = "https://api.mistral.ai/v1/ocr"
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    # Payload as per official documentation
    payload = {
        "model": "mistral-ocr-latest",
        "document": document_payload,
        "include_image_base64": True  # We are explicitly asking for images
    }
    print("This may take a moment...")
    
    try:
        with httpx.Client(timeout=600.0) as client:
            response = client.post(base_url, headers=headers, json=payload)
            
            print(f"+ API call completed with status code: {response.status_code}")
            
            if response.status_code == 200:
                result = response.json()
                
                # Save the full, raw response
                with open(output_json_file, 'w', encoding='utf-8') as f:
                    json.dump(result, f, indent=4)
                print(f"+ Full API response saved to: {output_json_file}")
                
                # Analyze the response for images
                print("\n--- Analyzing Response ---")
                pages = result.get("pages", [])
                total_images_found = 0
                if not pages:
                    print("Warning: The API response did not contain a 'pages' array.")
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
                    print(f"+ CONCLUSION: The API *did* return image data.")
                else:
                    print(f"- CONCLUSION: The API did NOT return any image data for this document.")
                print("="*50)

            else:
                print(f"- API Error: {response.text}")

    except Exception as e:
        print(f"An unexpected error occurred: {e}")

def main():
    """Main function with command line argument support."""
    parser = argparse.ArgumentParser(
        description="Debug script to test Mistral OCR API with URL or local PDF files.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Examples:\n"
               "  python debug_mistral.py                               # Use default URL\n"
               "  python debug_mistral.py https://example.com/doc.pdf   # Test with URL\n"
               "  python debug_mistral.py /path/to/local/document.pdf   # Test with local file"
    )
    parser.add_argument(
        "document", 
        nargs='?', 
        default=DEFAULT_DOCUMENT_URL,
        help="PDF document to test (URL or local file path). Default: %(default)s"
    )
    parser.add_argument(
        "output_json", 
        nargs='?', 
        default=DEFAULT_OUTPUT_JSON_FILE,
        help="Output JSON file for API response. Default: %(default)s"
    )
    
    args = parser.parse_args()
    debug_api_call(args.document, args.output_json)

if __name__ == "__main__":
    main()