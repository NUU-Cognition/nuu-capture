# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

OCR pipeline that converts PDF documents to structured Markdown using Mistral OCR API, followed by a two-stage formatting process. The system processes documents from URLs, extracts images, and applies progressive formatting improvements while maintaining zero information loss.

## Core Architecture

### Three-Module Structure
- **ocr_get/**: PDF processing and OCR extraction using Mistral API
- **ocr_fix/**: Two-stage formatting pipeline with zero-information-loss guarantee
- **txtfiles/**: Configuration files and formatting prompts

### Processing Pipeline Flow
1. **PDF Processing** (`ocr_get/process_pdf.py`) → Raw OCR + extracted images
2. **Image Link Fixing** (`ocr_fix/fix_markdown.py`) → Fixed image references  
3. **Stage 1** (`ocr_fix/stage1.py`) → Preprocessed, truncated content
4. **Stage 2** (`ocr_fix/stage2.py`) → LLM-enhanced formatting

## Common Commands

### Environment Setup
```bash
# Setup virtual environment and dependencies
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r txtfiles/requirements.md

# Configure API keys (required)
cp txtfiles/env_template.md .env
# Edit .env to add MISTRAL_API_KEY and GEMINI_API_KEY
```

### Full Pipeline Execution
```bash
# Interactive mode (recommended) - choose URL or local PDF from test_pdf/ folder
python ocr_get/process_pdf.py                               # Interactive selection
python ocr_fix/fix_markdown.py                              # Fix image links
python ocr_fix/stage1.py                                    # Stage 1 preprocessing
python ocr_fix/stage2.py                                    # Stage 2 LLM formatting

# Direct processing (URL)
python ocr_get/process_pdf.py https://example.com/doc.pdf   # OCR extraction from URL
python ocr_fix/fix_markdown.py                              # Fix image links
python ocr_fix/stage1.py                                    # Stage 1 preprocessing
python ocr_fix/stage2.py                                    # Stage 2 LLM formatting

# Direct processing (local file from test_pdf/)
python ocr_get/process_pdf.py test_pdf/document.pdf         # OCR extraction from local file
python ocr_fix/fix_markdown.py                              # Fix image links
python ocr_fix/stage1.py                                    # Stage 1 preprocessing
python ocr_fix/stage2.py                                    # Stage 2 LLM formatting
```

### Custom File Processing
```bash
# Force interactive mode with custom output directory
python ocr_get/process_pdf.py --interactive custom_output/

# PDF processing with custom output directory
python ocr_get/process_pdf.py test_pdf/document.pdf custom_output/

# Stage 1 with custom paths
python ocr_fix/stage1.py input.md output.md

# Stage 2 with custom paths  
python ocr_fix/stage2.py input.md output.md txtfiles/formatting_prompt.md

# Debug API with local file
python ocr_get/debug_mistral.py test_pdf/document.pdf debug_output.json
```

## Key Configuration Details

### API Dependencies
- **Mistral OCR API**: Required for PDF processing (`mistral-ocr-latest` model)
- **Google Gemini API**: Required for Stage 2 formatting (`gemini-1.5-pro-latest` model)
- Both API keys must be set in `.env` file

### Default File Paths
- **Local PDF Upload Directory**: `test_pdf/` (place PDFs here for local processing)
- **Input**: Document URL, local PDF file, or interactive selection
- **Output directory**: `document_ocr_test/` (customizable via command line)
- **Formatting prompt**: `txtfiles/formatting_prompt.md`

### Stage Processing Logic
- **Stage 1**: Removes appendix after References section, fixes OCR errors, joins broken paragraphs
- **Stage 2**: Section-by-section LLM processing with retry logic (3 attempts with exponential backoff)

## Important Implementation Notes

### Zero Information Loss Guarantee
Stage 1 preprocessing maintains all original content while fixing formatting. Stage 2 uses section-by-section processing to handle large documents without truncation.

### Error Handling Patterns
- Stage 2 implements comprehensive retry logic for API failures
- Failed sections fall back to original content to prevent data loss
- All scripts include detailed progress logging

### File Processing Capabilities
- **Interactive Mode**: Terminal menu to choose between URL or local file processing
- **URL Processing**: Direct processing from public PDF URLs
- **Local File Processing**: Base64 encoding and upload of PDFs from `test_pdf/` folder
- **Automatic Detection**: Script auto-detects input type (URL vs local file path)
- **File Selection**: Interactive menu displays available PDFs with file sizes
- **Image Extraction**: Images extracted as base64 from API response, saved with format detection (JPEG/PNG/GIF)
- **File Naming**: Images saved using pattern `page_{N}_image_{M}.{ext}`