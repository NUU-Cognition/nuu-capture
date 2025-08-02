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
python ocr_pipeline/process_pdf.py
```

### 6. Run the two-stage formatting pipeline
```bash
# Stage 1: Basic preprocessing and OCR fixes
python formatting_scripts/stage1.py

# Stage 2: Advanced LLM-based formatting
python formatting_scripts/stage2.py
```

## Two-Stage Formatting Pipeline

### Stage 1: Preprocessing (`stage1.py`)
- **OCR Error Fixes**: Repairs common OCR artifacts
- **Paragraph Formatting**: Joins broken paragraphs and fixes spacing
- **Document Truncation**: Removes appendix content after References
- **Input**: `saved_markdowns/processed_document.md`
- **Output**: `saved_markdowns/stage1_format.md`

### Stage 2: Advanced Formatting (`stage2.py`)
- **LLM-Based Processing**: Uses Gemini AI for intelligent formatting
- **Subheading Creation**: Converts topic keywords to proper headings
- **Figure/Table Caption Formatting**: Properly formats captions and labels
- **List Reformating**: Converts run-on lists to proper markdown lists
- **LaTeX Repair**: Fixes broken mathematical expressions
- **Input**: `saved_markdowns/stage1_format.md`
- **Output**: `saved_markdowns/stage2_format.md`

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

```python
from ocr_pipeline.simple_ocr_processor import SimpleOCRProcessor

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

### Running the Formatting Pipeline

```bash
# Run the complete pipeline
python formatting_scripts/stage1.py
python formatting_scripts/stage2.py

# Or run with custom file paths
python formatting_scripts/stage1.py input.md output.md
python formatting_scripts/stage2.py input.md output.md prompt.txt
```

## Project Structure

```
ocr_script_own/
├── formatting_scripts/          # Advanced formatting tools
│   ├── stage1.py               # Stage 1: Preprocessing
│   ├── stage2.py               # Stage 2: LLM-based formatting
│   ├── gemini_formatter.py     # Gemini-based formatter
│   └── markdown_formatter_safe.py # Safe markdown formatter
├── ocr_pipeline/               # OCR processing tools
│   ├── process_pdf.py          # PDF processing script
│   └── simple_ocr_processor.py # Core OCR processing logic
├── txtfiles/                   # Configuration and templates
│   ├── requirements.txt        # Python dependencies
│   ├── env_template.txt        # Environment template
│   └── formatting_prompt.txt   # Master prompt for Stage 2
├── saved_markdowns/            # Output directory
│   ├── processed_document.md   # Raw OCR output
│   ├── stage1_format.md        # Stage 1 output
│   └── stage2_format.md        # Final formatted output
├── .env                        # Environment variables (not in repo)
├── .gitignore                  # Git ignore rules
└── README.md                   # This file
```

## Formatting Features

### Stage 1 Features:
- ✅ **Zero information loss guaranteed**
- Fixes HTML line breaks (`<br>` → markdown)
- Repairs broken URLs (`https: //` → `https://`)
- Adds proper spacing after sentence endings
- Consolidates excessive blank lines
- Preserves all content: tables, math, references, images
- Removes appendix content after References section

### Stage 2 Features:
- **Subheading Creation**: Converts topic keywords to Level 3 headings
- **Topic Bolding**: Applies bold formatting to section keywords
- **Figure Caption Formatting**: Properly formats figure labels and captions
- **Table Caption Formatting**: Formats table captions and labels
- **List Reformating**: Converts run-on lists to proper markdown lists
- **LaTeX Repair**: Fixes broken mathematical expressions
- **Paragraph Coherence**: Reconstructs broken sentences and paragraphs

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

## Error Handling

The processor includes comprehensive error handling for:
- Missing API keys
- Invalid URLs
- Network timeouts
- API rate limits
- Malformed responses
- LLM processing failures (with retry logic)

## Limitations

- Currently supports document URLs only (not local file uploads)
- Requires internet connection for API calls
- Processing time depends on document size and complexity
- Stage 2 requires Google Gemini API access

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