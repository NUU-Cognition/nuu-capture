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
PDF_UPLOAD_DIR = Path("test_pdf")  # Directory for local PDF files

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

def list_available_pdfs():
    """List all PDF files in the test_pdf directory."""
    if not PDF_UPLOAD_DIR.exists():
        return []
    return [f for f in PDF_UPLOAD_DIR.iterdir() if f.suffix.lower() == '.pdf']

def interactive_pdf_selection():
    """Interactive menu to select PDF source (URL or local file)."""
    print("\n🔍 PDF Processing Options")
    print("=" * 40)
    print("1. Process PDF from URL")
    print("2. Process local PDF file")
    print("3. Use default URL (https://openreview.net/pdf?id=nAFBHoMpQs)")
    
    while True:
        try:
            choice = input("\nSelect an option (1-3): ").strip()
            
            if choice == '1':
                url = input("Enter PDF URL: ").strip()
                if not url:
                    print("❌ URL cannot be empty. Please try again.")
                    continue
                if not is_url(url):
                    print("❌ Invalid URL format. Please try again.")
                    continue
                return url
                
            elif choice == '2':
                available_pdfs = list_available_pdfs()
                if not available_pdfs:
                    print(f"❌ No PDF files found in {PDF_UPLOAD_DIR}")
                    print(f"   Please add PDF files to the {PDF_UPLOAD_DIR} folder and try again.")
                    continue
                
                print(f"\n📁 Available PDF files in {PDF_UPLOAD_DIR}:")
                for i, pdf_file in enumerate(available_pdfs, 1):
                    file_size = pdf_file.stat().st_size / (1024 * 1024)  # Size in MB
                    print(f"   {i}. {pdf_file.name} ({file_size:.1f} MB)")
                
                while True:
                    try:
                        pdf_choice = input(f"\nSelect PDF file (1-{len(available_pdfs)}): ").strip()
                        pdf_index = int(pdf_choice) - 1
                        if 0 <= pdf_index < len(available_pdfs):
                            selected_pdf = available_pdfs[pdf_index]
                            print(f"✅ Selected: {selected_pdf.name}")
                            return str(selected_pdf)
                        else:
                            print(f"❌ Please enter a number between 1 and {len(available_pdfs)}")
                    except ValueError:
                        print("❌ Please enter a valid number")
                        
            elif choice == '3':
                print(f"✅ Using default URL: {DEFAULT_DOCUMENT_URL}")
                return DEFAULT_DOCUMENT_URL
                
            else:
                print("❌ Invalid choice. Please enter 1, 2, or 3.")
                
        except KeyboardInterrupt:
            print("\n\n👋 Process cancelled by user.")
            exit(0)

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
               "  python process_pdf.py                                    # Interactive mode\n"
               "  python process_pdf.py --interactive                     # Force interactive mode\n"
               "  python process_pdf.py https://example.com/doc.pdf       # Process from URL\n"
               "  python process_pdf.py test_pdf/document.pdf             # Process local file\n"
               "  python process_pdf.py document.pdf custom_output/       # Custom output dir"
    )
    parser.add_argument(
        "document", 
        nargs='?', 
        help="PDF document to process (URL or local file path). If not provided, interactive mode starts."
    )
    parser.add_argument(
        "output_dir", 
        nargs='?', 
        default=DEFAULT_OUTPUT_DIR,
        help="Output directory for processed files. Default: %(default)s"
    )
    parser.add_argument(
        "--interactive", "-i",
        action="store_true",
        help="Force interactive mode even if document argument is provided"
    )
    
    args = parser.parse_args()
    output_dir = Path(args.output_dir)
    
    # Determine document input based on arguments
    if args.interactive or args.document is None:
        # Interactive mode
        document_input = interactive_pdf_selection()
    else:
        # Direct mode with provided argument
        document_input = args.document
    
    if not MISTRAL_API_KEY:
        raise ValueError("MISTRAL_API_KEY environment variable is required")

    print("\n🚀 Starting PDF Processing with Mistral OCR")
    print("=" * 50)
    
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
            print("\n📂 Next steps:")
            print("   1. Run: python ocr_fix/fix_markdown.py")
            print("   2. Run: python ocr_fix/stage1.py")
            print("   3. Run: python ocr_fix/stage2.py")

    except Exception as e:
        print(f"❌ An error occurred: {e}")

if __name__ == "__main__":
    main()