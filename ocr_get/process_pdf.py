#!/usr/bin/env python3
"""
Single-file script to process a PDF from a URL or local file and save outputs.
Includes detailed debugging prints.
"""
import os
import json
import httpx
import base64
import argparse
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv

# --- Load Environment Variables ---
load_dotenv()
MISTRAL_API_KEY = os.getenv("MISTRAL_API_KEY")

# --- Default Configuration ---
DEFAULT_DOCUMENT_URL = "https://openreview.net/pdf?id=nAFBHoMpQs"
DEFAULT_OUTPUT_DIR = Path("document_ocr_test")

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
        print(f"📄 Processing document from URL: {document_input}")
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
            
        print(f"📄 Processing local PDF file: {document_input}")
        base64_pdf = encode_pdf_to_base64(pdf_path)
        return {
            "type": "document_url",
            "document_url": f"data:application/pdf;base64,{base64_pdf}"
        }

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
    parser = argparse.ArgumentParser(
        description="Process PDF documents using Mistral OCR API.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Examples:\n"
               "  python process_pdf.py                                    # Use default URL\n"
               "  python process_pdf.py https://example.com/doc.pdf       # Process from URL\n"
               "  python process_pdf.py /path/to/local/document.pdf       # Process local file\n"
               "  python process_pdf.py document.pdf custom_output/       # Custom output dir"
    )
    parser.add_argument(
        "document", 
        nargs='?', 
        default=DEFAULT_DOCUMENT_URL,
        help="PDF document to process (URL or local file path). Default: %(default)s"
    )
    parser.add_argument(
        "output_dir", 
        nargs='?', 
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for processed files. Default: %(default)s"
    )
    
    args = parser.parse_args()
    document_input = args.document
    output_dir = Path(args.output_dir)
    
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY environment variable is required")

    print("🚀 Starting PDF Processing with Mistral OCR")
    print("==================================================")
    
    try:
        document_payload = prepare_document_payload(document_input)
    except Exception as e:
        print(f"❌ Error preparing document: {e}")
        return

    base_url = "https://api.mistral.ai/v1"
    headers = {
        "Authorization": f"Bearer {MISTRAL_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "mistral-ocr-latest",
        "document": document_payload,
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
                        
                        if save_image_from_data(image_data_str, page_index, image_index, output_dir):
                            images_saved_count += 1
            
            # Save the markdown content
            markdown_file_path = output_dir / "document_content.md"
            with open(markdown_file_path, 'w', encoding='utf-8') as f:
                f.write(markdown_content)

            print("\n✅ Document processing finished!")
            print(f"💾 All outputs saved to: {output_dir.resolve()}")
            print(f"📊 Processed {len(pages)} page(s) with {images_saved_count} image(s) extracted")
            print("\n✅ Processing task completed successfully!")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()