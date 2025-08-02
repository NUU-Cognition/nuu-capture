#!/usr/bin/env python3
"""
Process PDF from URL and save markdown output
"""

import os
from simple_ocr_processor import SimpleOCRProcessor

def process_pdf_url_and_save(document_url):
    """Process a PDF from URL and save markdown output."""
    
    # Output directory
    output_dir = "saved_markdowns"
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        print("🔍 Initializing OCR Processor...")
        processor = SimpleOCRProcessor()
        
        print(f"📄 Processing PDF from URL: {document_url}")
        result = processor.process_document_url(document_url)
        
        print("✅ PDF processed successfully!")
        print(f"📋 Pages processed: {result['pages_processed']}")
        print(f"📋 Model used: {result['model_used']}")
        print(f"📋 Images extracted: {len(result['images'])}")
        print(f"📋 Markdown length: {len(result['markdown_content'])}")
        
        # Save markdown to file
        output_file = os.path.join(output_dir, "processed_document.md")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(result['markdown_content'])
        
        print(f"💾 Markdown saved to: {output_file}")
        
        # Show preview
        if result['markdown_content']:
            print(f"\n📄 Markdown preview (first 500 chars):")
            print("-" * 50)
            print(result['markdown_content'][:500])
            print("-" * 50)
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Processing PDF with Mistral OCR")
    print("=" * 50)
    
    # OpenReview PDF URL
    document_url = "https://openreview.net/pdf?id=nAFBHoMpQs"
    
    success = process_pdf_url_and_save(document_url)
    
    if success:
        print("\n✅ PDF processing completed successfully!")
    else:
        print("\n❌ PDF processing failed!") 