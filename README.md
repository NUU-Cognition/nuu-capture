# OCR Pipeline with Two-Stage Formatting

A production-ready Python backend script that converts long-form PDF documents into structured Markdown format using the Mistral OCR API, followed by a two-stage formatting pipeline for optimal document quality.

## Features

- **Mistral OCR Integration**: Direct integration with Mistral AI's OCR API
- **Document URL Processing**: Process PDFs from public URLs
- **Two-Stage Formatting Pipeline**: Advanced formatting with zero information loss
- **Markdown Output**: Structured markdown with preserved formatting
- **Image Extraction**: Extract and reference images from documents
- **Safe Markdown Formatting**: Zero-information-loss formatting tools
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
pip install -r txtfiles/requirements.txt
```

### 4. Configure environment variables
Copy the environment template and add your API keys:
```bash
cp txtfiles/env_template.txt .env
# Edit .env and add your API keys:
# - MISTRAL_API_KEY (for OCR processing)
# - GEMINI_API_KEY (for advanced formatting)
```

### 5. Process a PDF document
```bash
python ocr_get/process_pdf.py
```

### 6. Run the two-stage formatting pipeline
```bash
# Stage 1: Basic preprocessing and OCR fixes
python ocr_fix/stage1.py

# Stage 2: Advanced LLM-based formatting
python ocr_fix/stage2.py
```

## Complete Process Flow

### Step 1: PDF Processing (`ocr_get/process_pdf.py`)
- **Input**: PDF document URL (currently set to OpenReview paper)
- **Process**: 
  - Calls Mistral OCR API with `mistral-ocr-latest` model
  - Extracts markdown content from each page
  - Saves images as base64-encoded files (JPEG/PNG/GIF)
  - Handles image data URI parsing and format detection
- **Output**: 
  - `document_ocr_test/document_content.md` (raw OCR output)
  - `document_ocr_test/page_X_image_Y.jpeg` (extracted images)

### Step 2: Image Link Fixing (`ocr_fix/fix_markdown.py`)
- **Input**: `document_ocr_test/document_content.md`
- **Process**: 
  - Finds all image tags in markdown
  - Replaces placeholder image links with correct saved filenames
  - Ensures proper image references
- **Output**: `document_ocr_test/pre_stage_1.md`

### Step 3: Stage 1 Preprocessing (`ocr_fix/stage1.py`)
- **Input**: `document_ocr_test/pre_stage_1.md`
- **Process**:
  - **Document Truncation**: Removes appendix content after References section
  - **OCR Error Fixes**: Repairs common OCR artifacts (e.g., `https: //` → `https://`)
  - **Paragraph Formatting**: Joins broken paragraphs and fixes spacing
  - **Zero Information Loss**: Preserves all original content
- **Output**: `document_ocr_test/stage_1_complete.md`

### Step 4: Stage 2 Advanced Formatting (`ocr_fix/stage2.py`)
- **Input**: `document_ocr_test/stage_1_complete.md`
- **Process**:
  - **LLM-Based Processing**: Uses Gemini AI for intelligent formatting
  - **Section-by-Section Processing**: Splits document into logical sections
  - **Subheading Creation**: Converts topic keywords to proper headings
  - **Figure/Table Caption Formatting**: Properly formats captions and labels
  - **List Reformating**: Converts run-on lists to proper markdown lists
  - **LaTeX Repair**: Fixes broken mathematical expressions
  - **Retry Logic**: Handles API failures with exponential backoff
- **Output**: `document_ocr_test/final_formatted.md`

## Configuration

### Environment Variables

Create a `.env` file with the following variables:

```env
# Mistral AI API Configuration
MISTRAL_API_KEY=your_mistral_api_key_here

# Google Gemini API Configuration
GEMINI_API_KEY=your_gemini_api_key_here

# Directory Configuration
UPLOAD_DIR=temp_uploads
EXTRACTED_IMAGES_DIR=extracted_images

# API Configuration
HOST=0.0.0.0
PORT=8000
```

## Usage

### Processing PDFs from URLs

The main processing script (`ocr_get/process_pdf.py`) is configured to process a specific OpenReview paper:

```python
# Current configuration in process_pdf.py
DOCUMENT_URL = "https://openreview.net/pdf?id=nAFBHoMpQs"
OUTPUT_DIR = Path("document_ocr_test")
```

To process a different document, modify the `DOCUMENT_URL` variable in the script.

### Running the Complete Pipeline

```bash
# 1. Process PDF and extract content
python ocr_get/process_pdf.py

# 2. Fix image links in markdown
python ocr_fix/fix_markdown.py

# 3. Run Stage 1 preprocessing
python ocr_fix/stage1.py

# 4. Run Stage 2 advanced formatting
python ocr_fix/stage2.py
```

### Custom File Paths

All scripts support custom input/output paths:

```bash
# Stage 1 with custom paths
python ocr_fix/stage1.py input.md output.md

# Stage 2 with custom paths
python ocr_fix/stage2.py input.md output.md prompt.txt
```

## Project Structure

```
ocr_script_own/
├── ocr_get/                    # OCR processing tools
│   ├── process_pdf.py          # Main PDF processing script
│   └── debug_mistral.py        # Debug script for API testing
├── ocr_fix/                    # Formatting pipeline
│   ├── stage1.py               # Stage 1: Preprocessing
│   ├── stage2.py               # Stage 2: LLM-based formatting
│   └── fix_markdown.py         # Image link fixing
├── txtfiles/                   # Configuration and templates
│   ├── requirements.txt        # Python dependencies
│   ├── env_template.txt        # Environment template
│   └── formatting_prompt.txt   # Master prompt for Stage 2
├── document_ocr_test/          # Output directory
│   ├── document_content.md     # Raw OCR output
│   ├── pre_stage_1.md         # After image link fixing
│   ├── stage_1_complete.md    # Stage 1 output
│   ├── final_formatted.md      # Final formatted output
│   └── page_X_image_Y.jpeg    # Extracted images
├── example_format_md/          # Example output
│   └── formatted_document.md   # Sample formatted document
├── test_pdf/                   # Test PDF directory
├── venv/                       # Virtual environment
├── .env                        # Environment variables (not in repo)
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Formatting Features

### Stage 1 Features:
- ✅ **Zero information loss guaranteed**
- **Document Truncation**: Removes appendix content after References section
- **OCR Error Fixes**: Repairs common OCR artifacts
- **Paragraph Joining**: Consolidates broken paragraphs
- **Spacing Normalization**: Removes excessive blank lines
- **Preserves All Content**: Tables, math, references, images

### Stage 2 Features:
- **Subheading Creation**: Converts topic keywords to Level 3 headings
- **Topic Bolding**: Applies bold formatting to section keywords
- **Figure Caption Formatting**: Properly formats figure labels and captions
- **Table Caption Formatting**: Formats table captions and labels
- **List Reformating**: Converts run-on lists to proper markdown lists
- **LaTeX Repair**: Fixes broken mathematical expressions
- **Paragraph Coherence**: Reconstructs broken sentences and paragraphs
- **Section-by-Section Processing**: Handles large documents efficiently

## API Response Structure

The Mistral OCR API returns a structured response:

```python
{
    "pages": [
        {
            "markdown": "Page content in markdown...",
            "images": [
                {
                    "image_base64": "base64_encoded_image_data",
                    "type": "image/jpeg"
                }
            ]
        }
    ]
}
```

## Error Handling

The pipeline includes comprehensive error handling for:
- Missing API keys
- Invalid URLs
- Network timeouts
- API rate limits
- Malformed responses
- LLM processing failures (with retry logic)
- File I/O errors
- Image processing errors

## Debugging Tools

### Debug Mistral API (`ocr_get/debug_mistral.py`)
- Tests Mistral OCR API connectivity
- Saves raw API responses to JSON
- Analyzes image extraction results
- Useful for troubleshooting API issues

### Test Data
- `test.json`: Sample API response for testing
- `document_ocr_test/`: Contains processed outputs for analysis

## Limitations

- Currently supports document URLs only (not local file uploads)
- Requires internet connection for API calls
- Processing time depends on document size and complexity
- Stage 2 requires Google Gemini API access
- Image extraction depends on API response format

## Dependencies

Key Python packages:
- `httpx`: HTTP client for API calls
- `python-dotenv`: Environment variable management
- `google-generativeai`: Gemini AI integration
- `Pillow`: Image processing (if needed)
- `fastapi`, `uvicorn`: Web framework (for future API endpoints)

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests if applicable
5. Submit a pull request

## License

All components are part of NUU Cognition. NUU Capture is an element of NUU Cognition.

## Acknowledgments

- Mistral AI for providing the OCR API
- Google Gemini for advanced formatting capabilities
- OpenReview for the test document 