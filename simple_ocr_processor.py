#!/usr/bin/env python3
"""
Simple OCR Processor using Mistral API
"""

import os
import json
import httpx
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleOCRProcessor:
    """Simple OCR processor using Mistral API."""
    
    def __init__(self):
        self.api_key = os.getenv("MISTRAL_API_KEY")
        if not self.api_key:
            raise ValueError("MISTRAL_API_KEY environment variable is required")
        
        self.base_url = "https://api.mistral.ai/v1"
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
    
    def process_document_url(self, document_url, pages=None, include_images=True):
        """Process a document from URL using OCR."""
        
        payload = {
            "model": "mistral-ocr-latest",
            "document": {
                "type": "document_url",
                "document_url": document_url
            },
            "include_image_base64": include_images
        }
        
        if pages:
            payload["pages"] = pages
        
        try:
            with httpx.Client() as client:
                response = client.post(
                    f"{self.base_url}/ocr",
                    headers=self.headers,
                    json=payload,
                    timeout=600.0  # 10 minutes timeout
                )
                
                if response.status_code == 200:
                    result = response.json()
                    return self._process_ocr_result(result)
                else:
                    raise Exception(f"OCR API error: {response.status_code} - {response.text}")
                    
        except Exception as e:
            raise Exception(f"Error processing document: {str(e)}")
    
    def _process_ocr_result(self, result):
        """Process the OCR result into structured format."""
        
        processed_result = {
            "markdown_content": "",
            "images": [],
            "pages_processed": 0,
            "model_used": result.get("model", "unknown")
        }
        
        # Extract markdown from all pages
        if "pages" in result:
            pages = result["pages"]
            processed_result["pages_processed"] = len(pages)
            
            for page in pages:
                if "markdown" in page:
                    processed_result["markdown_content"] += page["markdown"] + "\n\n"
                
                # Extract images if present
                if "images" in page and page["images"]:
                    for img in page["images"]:
                        processed_result["images"].append({
                            "page": page.get("index", 0),
                            "image_data": img.get("base64", ""),
                            "image_type": img.get("type", "unknown")
                        })
        
        # Also check for document_annotation (full document text)
        if "document_annotation" in result and result["document_annotation"]:
            processed_result["full_text"] = result["document_annotation"]
        
        return processed_result

# Example usage
if __name__ == "__main__":
    processor = SimpleOCRProcessor()
    
    # Test with URL (existing functionality)
    print("Testing with URL...")
    result = processor.process_document_url("https://www.w3.org/WAI/ER/tests/xhtml/testfiles/resources/pdf/dummy.pdf")
    print(f"✅ URL test successful: {len(result['markdown_content'])} characters") 