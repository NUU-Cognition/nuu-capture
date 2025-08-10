# Universal Research Paper OCR Pipeline

A production-ready Python backend script that converts research papers and academic documents from PDF to structured Markdown format. Features Mistral OCR API integration with an advanced AI-powered formatting pipeline designed to work across all research disciplines while preserving author intent and ensuring zero information loss.

## Features

- **Universal Research Paper Support**: Works across all academic disciplines (Life Sciences, Computer Science, Physics, Social Sciences, etc.)
- **Mistral OCR Integration**: High-quality OCR extraction using Mistral AI's latest OCR model
- **Intelligent Document Processing**: Auto-detects PDF filenames and creates organized output folders
- **Advanced AI Formatting**: Universal research prompt that adapts to different paper styles and conventions
- **Zero Information Loss**: Preserves 100% of original content while improving formatting
- **Mathematical Expression Repair**: Fixes LaTeX formulas, citations, and scientific notation
- **Figure & Table Processing**: Proper caption formatting and table reconstruction
- **Error Handling**: Comprehensive retry logic and fallback mechanisms
- **Flexible Input Options**: Process from URLs or local PDF files

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
# Interactive mode - choose between URL or local file
python ocr_get/process_pdf.py

# Or process a specific PDF from test_pdf/ folder
python ocr_get/process_pdf.py test_pdf/your_paper.pdf

# Or process from a URL
python ocr_get/process_pdf.py https://example.com/paper.pdf
```

### 6. Run the complete formatting pipeline
```bash
# Fix image links (auto-detects most recent folder)
python ocr_fix/fix_markdown.py

# Stage 1: Basic preprocessing and OCR fixes
python ocr_fix/stage1.py

# Stage 2: Universal research paper formatting
python ocr_fix/stage2.py
```

## Complete Process Flow

### Step 1: PDF Processing (`ocr_get/process_pdf.py`)
- **Input**: PDF document from URL, local file, or interactive selection
- **Process**: 
  - Auto-detects PDF filename and creates organized output folder (e.g., `demo_paper_2/`)
  - Calls Mistral OCR API with `mistral-ocr-latest` model
  - Extracts markdown content with high accuracy
  - Saves images as base64-encoded files with format detection (JPEG/PNG/GIF)
  - Handles complex academic content (equations, tables, figures)
- **Output**: 
  - `{pdf_name}/document_content.md` (raw OCR output)
  - `{pdf_name}/page_X_image_Y.{format}` (extracted images)

### Step 2: Image Link Fixing (`ocr_fix/fix_markdown.py`)
- **Input**: `{pdf_name}/document_content.md`
- **Process**: 
  - Auto-detects most recent output folder
  - Matches image tags with saved image files
  - Fixes image references for proper markdown display
- **Output**: `{pdf_name}/pre_stage_1.md`

### Step 3: Stage 1 Preprocessing (`ocr_fix/stage1.py`)
- **Input**: `{pdf_name}/pre_stage_1.md`
- **Process**:
  - **Smart Document Truncation**: Removes appendix content after References section
  - **OCR Error Fixes**: Repairs common OCR artifacts (spacing, URLs, etc.)
  - **Paragraph Reconstruction**: Intelligently joins broken paragraphs
  - **Zero Information Loss**: Preserves all original research content
- **Output**: `{pdf_name}/stage_1_complete.md`

### Step 4: Universal Research Formatting (`ocr_fix/stage2.py`)
- **Input**: `{pdf_name}/stage_1_complete.md`
- **Process**:
  - **Universal Research Prompt**: Adapts to different academic disciplines and styles
  - **Mathematical Expression Repair**: Fixes LaTeX formulas and scientific notation
  - **Citation Enhancement**: Repairs reference formatting while preserving author style
  - **Scientific Content Formatting**: Species names, chemical formulas, gene names
  - **Figure/Table Processing**: Proper caption formatting and table reconstruction
  - **Cross-Reference Creation**: Internal document linking
  - **Style Preservation**: Maintains author's original formatting preferences
  - **Intelligent Error Handling**: Retry logic with fallback to preserve content
- **Output**: `{pdf_name}/final_formatted.md`

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