# OCR Pipeline with Mistral AI

A production-ready Python backend script that converts long-form PDF documents into structured Markdown format using the Mistral OCR API.

## Features

- **Mistral OCR Integration**: Direct integration with Mistral AI's OCR API
- **Document URL Processing**: Process PDFs from public URLs
- **Markdown Output**: Structured markdown with preserved formatting
- **Image Extraction**: Extract and reference images from documents
- **Safe Markdown Formatting**: Zero-information-loss formatting tool
- **Error Handling**: Comprehensive error handling and logging
- **Environment Management**: Secure API key management

## Quick Start

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd ocr_script_own
```

### 2. Set up virtual environment
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
Copy the environment template and add your Mistral API key:
```bash
cp env_template.txt .env
# Edit .env and add your MISTRAL_API_KEY
```

### 5. Test the OCR processor
```bash
python process_pdf.py
```

### 6. Format the generated markdown (optional)
```bash
python markdown_formatter_safe.py saved_markdowns/processed_document.md
```

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Mistral AI API Configuration
MISTRAL_API_KEY=your_mistral_api_key_here

# Directory Configuration
UPLOAD_DIR=temp_uploads
EXTRACTED_IMAGES_DIR=extracted_images

# API Configuration
HOST=0.0.0.0
PORT=8000
```

## Usage

### Processing PDFs from URLs

```python
from simple_ocr_processor import SimpleOCRProcessor

# Initialize the processor
processor = SimpleOCRProcessor()

# Process a PDF from URL
result = processor.process_document_url(
    document_url="https://example.com/document.pdf",
    pages=[0, 1, 2],  # Optional: specific pages
    include_images=True  # Optional: extract images
)

# Access results
print(f"Pages processed: {result['pages_processed']}")
print(f"Markdown content: {result['markdown_content']}")
print(f"Images extracted: {len(result['images'])}")
```

### Saving Results

```python
import os

# Save markdown to file
output_dir = "saved_markdowns"
os.makedirs(output_dir, exist_ok=True)

with open(os.path.join(output_dir, "processed_document.md"), 'w', encoding='utf-8') as f:
    f.write(result['markdown_content'])
```

### Formatting the Generated Markdown

The OCR output may contain formatting issues. Use the safe markdown formatter to clean up the text with zero information loss:

```python
from markdown_formatter_safe import SafeMarkdownFormatter

# Initialize the safe formatter
formatter = SafeMarkdownFormatter()

# Format the markdown text safely
formatted_text = formatter.format_markdown_safe(markdown_content)

# Save the formatted version
with open("formatted_document.md", 'w', encoding='utf-8') as f:
    f.write(formatted_text)
```

**Safe Formatting Features:**
- ✅ **Zero information loss guaranteed**
- Fixes HTML line breaks (`<br>` → markdown)
- Repairs broken URLs (`https: //` → `https://`)
- Adds proper spacing after sentence endings
- Consolidates excessive blank lines
- Preserves all content: tables, math, references, images
- Conservative approach - only safe formatting changes

## API Response Structure

The OCR processor returns a structured response:

```python
{
    "markdown_content": "Full markdown text...",
    "images": [
        {
            "page": 0,
            "image_data": "base64_encoded_image",
            "image_type": "jpeg"
        }
    ],
    "pages_processed": 27,
    "model_used": "mistral-ocr-2505-completion"
}
```

## Project Structure

```
ocr_script_own/
├── simple_ocr_processor.py    # Core OCR processing logic
├── process_pdf.py             # Example usage script
├── markdown_formatter_safe.py # Safe markdown formatting tool
├── requirements.txt           # Python dependencies
├── .env                      # Environment variables (not in repo)
├── .gitignore               # Git ignore rules
├── env_template.txt         # Environment template
├── test_pdf/               # Test PDF files (not in repo)
├── saved_markdowns/        # Output directory (not in repo)
└── venv/                   # Virtual environment (not in repo)
```

## Error Handling

The processor includes comprehensive error handling for:
- Missing API keys
- Invalid URLs
- Network timeouts
- API rate limits
- Malformed responses

## Limitations

- Currently supports document URLs only (not local file uploads)
- Requires internet connection for API calls
- Processing time depends on document size and complexity

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

[Add your license here]

## Acknowledgments

- Mistral AI for providing the OCR API
- OpenReview for the test document 