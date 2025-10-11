# Universal Research Paper OCR Pipeline

A production-ready Python backend script that converts research papers and academic documents from PDF to structured Markdown format, with advanced JSON structure parsing capabilities. Features Mistral OCR API integration with an advanced AI-powered formatting pipeline designed to work across all research disciplines while preserving author intent and ensuring zero information loss.

## Features

- **🚀 Unified Pipeline**: Single command processing - run the entire 4-stage pipeline with one command
- **📄 Advanced JSON Parser v3.2**: Smart element merging, structured references, individual author parsing, and enhanced table detection
- **Universal Research Paper Support**: Works across all academic disciplines (Life Sciences, Computer Science, Physics, Social Sciences, etc.)
- **Mistral OCR Integration**: High-quality OCR extraction using Mistral AI's latest OCR model
- **Intelligent Document Processing**: Auto-detects PDF filenames and creates organized output folders
- **Advanced AI Formatting**: Universal research prompt that adapts to different paper styles and conventions
- **Zero Information Loss**: Preserves 100% of original content while improving formatting
- **Mathematical Expression Repair**: Fixes LaTeX formulas, citations, and scientific notation
- **Figure & Table Processing**: Proper caption formatting and table reconstruction
- **Error Handling**: Comprehensive retry logic and fallback mechanisms
- **Flexible Input Options**: Process from URLs or local PDF files
- **Progress Tracking**: Real-time progress updates and detailed logging for each processing stage
- **Structured Output**: Convert markdown to categorized JSON elements with sub-element extraction

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
pip install -r config/requirements.md
```

### 4. Configure environment variables
Copy the environment template and add your API keys:
```bash
cp config/env_template.md .env
# Edit .env and add your API keys:
# - MISTRAL_API_KEY (for OCR processing)
# - GEMINI_API_KEY (for advanced formatting)
```

### 5. Run the Complete Pipeline (Unified Script)
**NEW: Single Command Processing** - Run the entire pipeline with one command:
```bash
# Process a local PDF file
python unified_pipeline.py output/test_pdf/bio_paper_1.pdf

# Process from a URL
python unified_pipeline.py https://example.com/paper.pdf

# Process with custom output directory
python unified_pipeline.py output/test_pdf/bio_paper_1.pdf my_custom_folder
```

**The unified script automatically runs all 4 stages:**
1. ✅ PDF Processing (OCR extraction)
2. ✅ Image Link Fixing 
3. ✅ Stage 1 Preprocessing
4. ✅ Stage 2 LLM Formatting

### Alternative: Manual Step-by-Step Processing
If you prefer to run each stage individually:
```bash
# Step 1: PDF Processing
python stages/01_extract/process_pdf.py output/test_pdf/your_paper.pdf

# Step 2: Fix image links (auto-detects most recent folder)
python stages/01_extract/fix_markdown.py

# Step 3: Stage 1 preprocessing and OCR fixes
python stages/02_preprocess/stage1.py

# Step 4: Stage 2 universal research paper formatting
python stages/03_format/stage2.py
```

## Complete Process Flow

### Step 1: PDF Processing (`stages/01_extract/process_pdf.py`)
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

### Step 2: Image Link Fixing (`stages/01_extract/fix_markdown.py`)
- **Input**: `{pdf_name}/document_content.md`
- **Process**: 
  - Auto-detects most recent output folder
  - Matches image tags with saved image files
  - Fixes image references for proper markdown display
- **Output**: `{pdf_name}/pre_stage_1.md`

### Step 3: Stage 1 Preprocessing (`stages/02_preprocess/stage1.py`)
- **Input**: `{pdf_name}/pre_stage_1.md`
- **Process**:
  - **Universal Document Truncation**: Intelligently removes post-references content (acknowledgments, author affiliations, etc.) while adapting to different paper structures
  - **Enhanced OCR Error Fixes**: Repairs common OCR artifacts including:
    - Spacing issues: `https: //` → `https://`
    - Ligature fixes: `ﬁ` → `fi`, `ﬂ` → `fl`
    - Mathematical expressions: `{{ }}^{{133}}` → `^133`
  - **Hybrid Paragraph Reconstruction**: Uses advanced regex pattern detection with line-by-line processing to:
    - Intelligently join broken paragraphs while preserving structural elements
    - Detect comprehensive range of markdown elements (headings, lists, tables, citations, figures)
    - Maintain precise control over paragraph buffering and formatting
  - **Zero Information Loss**: Preserves all original research content in main document body
- **Output**: `{pdf_name}/stage_1_complete.md`

### Step 4: Universal Research Formatting (`stages/03_format/stage2.py`)
- **Input**: `{pdf_name}/stage_1_complete.md`
- **Process**:
  - **Universal Research Prompt**: Adapts to different academic disciplines and styles using `config/universal_research_prompt.md`
  - **Section-by-Section Processing**: Intelligently splits document into logical sections for optimal LLM processing
  - **Mathematical Expression Repair**: Fixes LaTeX formulas and scientific notation (e.g., `$^{133}$` → `<sup>133</sup>`)
  - **Citation Enhancement**: Repairs reference formatting while preserving author style (`^{11--13,26,19,38}` → `^11-13,19,26,38`)
  - **Scientific Content Formatting**: Species names, chemical formulas, gene names (`SCGB3A2` → `*SCGB3A2*`)
  - **Figure/Table Processing**: Creates proper figure references (`![Figure 1](#figure-1)`)
  - **Cross-Reference Creation**: Internal document linking and navigation
  - **Style Preservation**: Maintains author's original formatting preferences
  - **Intelligent Error Handling**: 3-attempt retry logic with exponential backoff and fallback to preserve content
- **Output**: `{pdf_name}/final_formatted.md`

### Step 5: JSON Structure Parsing (`stages/04_parse/parser_v3.py`) - **v3.2**
- **Input**: `{pdf_name}/final_formatted.md` or any markdown document
- **Process**:
  - **6-Stage Architecture**: Preprocessing → Segmentation → Classification → Detection → Extraction → Validation
  - **High-Accuracy Classification**: Deterministic hierarchical classification with 11 element types
  - **Smart Element Merging**: Automatic caption integration for figures and tables
  - **Refined Author Parsing**: Individual author extraction with affiliations and contact info
  - **Context-Aware LaTeX**: Display math only ($$...$$), inline math preserved in paragraphs
  - **Structured References**: Single consolidated node with parsed reference entries
  - **Enhanced Table Detection**: Multi-line table preservation with proper row segmentation
  - **Sub-Element Extraction**: Inline citations, author fields, LaTeX reference keys
  - **Element Types Supported**:
    - **Headings**: Levels 1-6 with hierarchy tracking
    - **Overlay blocks**: Special `(>>)` syntax support
    - **Code blocks**: With automatic language detection
    - **Abstract**: Position-aware detection
    - **Author sections**: Individual author objects with name/institution/contact/website
    - **Tables**: Proper multi-line detection with optional captions
    - **Figures/Images**: With automatic caption merging
    - **LaTeX formulas**: Display math only (not inline)
    - **Lists**: Bullet and numbered with item extraction
    - **References**: Consolidated single node with structured [id, content] entries
    - **Paragraphs**: With inline citations and inline math preservation
- **Output**: `output_structure.json` with categorized elements and metadata

#### JSON Parser Usage
```bash
# Basic usage
cd stages/04_parse
python parser_v3.py ../../output/example_format_md/test_document.md -o output.json

# With custom configuration
python parser_v3.py input.md -c config.yaml -o output.json
```

#### JSON Output Schema

The parser generates structured JSON with the following element formats:

**Author Section** - Individual author list:
```json
{
  "element_type": "author_section",
  "metadata": {"block_index": 1},
  "author_fields": [
    {
      "name": "Emily Jin",
      "institution": "Stanford University",
      "contact": "emily@stanford.edu",
      "website": "https://emilyjin.com"
    }
  ]
}
```

**Figure/Table with Caption** - Merged caption field:
```json
{
  "element_type": "figure_image",
  "content": "![Figure 1](img-0.jpeg)",
  "caption": "**Figure 1:** Description of the figure...",
  "metadata": {"block_index": 8}
}
```

**References Section** - Single consolidated node:
```json
{
  "element_type": "references",
  "metadata": {"block_index": 110},
  "references": [
    {
      "id": 1,
      "content": "[1] Author et al. Paper title. Venue, Year."
    },
    {
      "id": 2,
      "content": "[2] Another Author. Another paper. Conference, 2024."
    }
  ]
}
```

**LaTeX Formula** - Display math only:
```json
{
  "element_type": "latex_formula",
  "content": "$$E = mc^2$$",
  "metadata": {"block_index": 52}
}
```

**Paragraph** - Inline math and citations preserved:
```json
{
  "element_type": "paragraph",
  "content": "We use the equation $x = y + z$ to calculate...",
  "metadata": {"block_index": 15},
  "inline_citations": [
    {"id": "1, 2"},
    {"id": "5"}
  ]
}
```

**Table** - Multi-line preservation:
```json
{
  "element_type": "table",
  "content": "| Column 1 | Column 2 |\n|----------|----------|\n| Data 1   | Data 2   |",
  "metadata": {"block_index": 19}
}
```

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

### Unified Pipeline (Recommended)

The easiest way to process documents is using the unified pipeline script:

```bash
# Activate virtual environment first
source venv/bin/activate

# Process a local PDF file
python unified_pipeline.py test_pdf/bio_paper_1.pdf

# Process from a URL
python unified_pipeline.py https://example.com/research_paper.pdf

# Process with custom output directory
python unified_pipeline.py test_pdf/bio_paper_1.pdf custom_output_folder
```

The unified script provides:
- ✅ **Automated processing**: Runs all 4 stages sequentially
- ✅ **Progress tracking**: Real-time updates for each stage
- ✅ **Error handling**: Stops on errors with detailed messages
- ✅ **Environment validation**: Checks API keys and dependencies
- ✅ **File verification**: Confirms each stage completes successfully

### Manual Processing (Individual Scripts)

If you prefer to run each stage individually, the individual processing scripts support multiple input methods:

**Interactive Mode (Recommended)**:
```bash
python stages/01_extract/process_pdf.py
# Displays a menu to choose between URL input or local file selection
```

**Direct URL Processing**:
```bash
python stages/01_extract/process_pdf.py https://example.com/research_paper.pdf
```

**Local PDF Processing**:
```bash
python stages/01_extract/process_pdf.py output/test_pdf/my_paper.pdf
# Automatically creates output folder named "my_paper/"
```

**Custom Output Directory**:
```bash
python stages/01_extract/process_pdf.py output/test_pdf/paper.pdf custom_output_folder/
```

All methods automatically create output folders based on the PDF filename (e.g., `demo_paper_2.pdf` → `demo_paper_2/` folder).

### Running the Complete Pipeline

```bash
# 1. Process PDF and extract content
python stages/01_extract/process_pdf.py

# 2. Fix image links in markdown
python stages/01_extract/fix_markdown.py

# 3. Run Stage 2 preprocessing
python stages/02_preprocess/stage1.py

# 4. Run Stage 3 advanced formatting
python stages/03_format/stage2.py
```

### Custom File Paths

All scripts support custom input/output paths:

```bash
# Stage 2 with custom paths
python stages/02_preprocess/stage1.py input.md output.md

# Stage 3 with custom paths
python stages/03_format/stage2.py input.md output.md prompt.md
```

## Project Structure

```
ocr_script_own/
├── unified_pipeline.py         # 🚀 Single command for complete pipeline
├── stages/                     # 📁 Organized by processing stages
│   ├── 01_extract/            # Stage 1: PDF processing & OCR extraction
│   │   ├── process_pdf.py     # Main PDF processing script
│   │   ├── fix_markdown.py    # Image link fixing
│   │   └── debug_mistral.py   # Debug script for API testing
│   ├── 02_preprocess/         # Stage 2: Preprocessing & OCR fixes
│   │   └── stage1.py          # OCR fixes, truncation, paragraph reconstruction
│   ├── 03_format/             # Stage 3: LLM-based formatting
│   │   └── stage2.py          # Advanced formatting using Gemini AI
│   └── 04_parse/              # Stage 4: JSON structure parsing (v3.2)
│       ├── parser_v3.py       # Main parser with smart merging & structured output
│       ├── regex_patterns.py  # Centralized regex definitions
│       ├── config.yaml        # Tunable configuration parameters
│       ├── test_output.json   # Sample parsed output
│       ├── TEMP_SYNTAX.MD     # Element type specifications
│       └── docs/
│           └── PARSER_DESIGN.md  # Architecture documentation
├── config/                    # 📁 Configuration and templates
│   ├── requirements.md        # Python dependencies
│   ├── env_template.md        # Environment template
│   ├── universal_research_prompt.md  # Universal research prompt for Stage 3
│   └── cursor_prompt.txt      # Development prompt template
├── output/                    # 📁 Generated outputs and test data
│   ├── test_pdf/              # Sample PDF files for testing
│   └── example_format_md/     # Example output
│       └── test_document.md   # Sample formatted document
├── utils/                     # 📁 Shared utilities
│   └── types.py               # Type definitions
├── {pdf_name}/                # 📁 Output directory (auto-generated from PDF filename)
│   ├── document_content.md    # Raw OCR output
│   ├── pre_stage_1.md         # After image link fixing
│   ├── stage_1_complete.md    # Stage 2 output
│   ├── final_formatted.md     # Stage 3 output
│   └── page_X_image_Y.jpeg    # Extracted images
├── venv/                      # Virtual environment
├── .env                       # Environment variables (not in repo)
├── .gitignore                 # Git ignore rules
└── README.md                  # This file
```

## Formatting Features

### Stage 1 Features:
- ✅ **Zero information loss guaranteed**
- **Universal Document Truncation**: Intelligently removes post-references content across different paper structures
- **Enhanced OCR Error Fixes**: Comprehensive repair system including:
  - URL spacing fixes (`https: //` → `https://`)
  - Unicode ligature corrections (`ﬁ` → `fi`, `ﬂ` → `fl`)
  - Mathematical expression cleanup (`{{ }}^{{133}}` → `^133`)
- **Hybrid Paragraph Reconstruction**: Advanced dual-approach system combining:
  - Comprehensive regex pattern detection for structural elements
  - Line-by-line processing for maintainable control flow
  - Enhanced detection of citations, species names, figure captions, and section headers
- **Content Preservation**: Maintains all tables, equations, references, images, and scientific notation
- **Automatic Path Detection**: Finds and processes the most recent output directory

### Stage 2 Features:
- ✅ **Universal Research Paper Support**: Adapts to any academic discipline automatically
- **Mathematical Expression Enhancement**: Converts LaTeX to proper HTML (`$^{133}$` → `<sup>133</sup>`)
- **Scientific Content Formatting**: Proper italicization of gene names, species, etc. (`SCGB3A2` → `*SCGB3A2*`)
- **Citation Format Repair**: Fixes malformed references (`^{11--13,26,19,38}` → `^11-13,19,26,38`)
- **Figure Reference Creation**: Creates clickable figure links (`![Figure 1](#figure-1)`)
- **Professional Typography**: Smart quotes, proper em-dashes, spacing improvements
- **Section-by-Section Processing**: Handles large documents efficiently without truncation
- **Retry Logic**: 3-attempt processing with exponential backoff for reliability
- **Zero Information Loss**: Fallback mechanisms preserve all content if processing fails

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

### Debug Mistral API (`stages/01_extract/debug_mistral.py`)
- Tests Mistral OCR API connectivity
- Saves raw API responses to JSON
- Analyzes image extraction results
- Useful for troubleshooting API issues

### Test Data
- `test.json`: Sample API response for testing
- `document_ocr_test/`: Contains processed outputs for analysis

## Recent Updates (v3.2 Parser)

### JSON Parser v3.2 Major Updates:

#### 🎯 Smart Element Merging
- **Figure/Table Captions**: Automatically merges caption paragraphs into parent elements
  - Detects `**Figure X:**` and `**Table X:**` patterns
  - Creates unified `caption` field for cleaner output
  - Reduces element count by ~15-20%

#### 👥 Restructured Author Parsing
- **Individual Author Objects**: Parses bolded names (`**Name**`) into separate entries
- **Automatic Metadata Extraction**: Detects institutions, emails, and websites
- **List-Based Output**: `author_fields` is now an array of author objects
- **No Content Field**: Removes redundant content, keeps only structured data

#### 📐 Refined LaTeX Detection
- **Display Math Only**: Detects standalone formulas (`$$...$$`, `\[...\]`, `\begin{equation}`)
- **Inline Math Preservation**: Paragraphs with `$x = y$` remain as paragraphs
- **Fewer False Positives**: Avoids misclassifying "$100" as LaTeX

#### 📚 Consolidated References
- **Single References Node**: Merges all reference entries into one element
- **Structured Parsing**: Extracts `[id]` and content into separate fields
- **Multi-Line Support**: Handles references spanning multiple lines
- **Array-Based Output**: `references` field contains list of {id, content} objects

#### 📊 Enhanced Table Detection
- **Multi-Line Preservation**: Tables no longer collapsed into single lines
- **Improved Row Detection**: Preserves table structure during preprocessing
- **Consistent Detection**: Tables with 2+ pipe characters per line
- **Caption Support**: Same auto-merge functionality as figures

### Technical Improvements:
- Preprocessing now preserves structural elements (tables, lists, headings)
- Enhanced `_segment_blocks()` with table-aware merging logic
- New helper methods: `_parse_individual_authors()` and `_parse_references_list()`
- `_model_document_structure()` creates consolidated references element
- Post-processing caption merger in `_validate_and_postprocess()`
- Updated `ParseConfig` dataclass with 9 new configuration parameters

## Limitations

- Requires internet connection for API calls to Mistral OCR and Google Gemini
- Processing time depends on document size and complexity (typically 2-10 minutes for research papers)
- Stage 2 requires Google Gemini API access with sufficient quota
- Image extraction quality depends on source PDF quality and API response format
- Very large documents (>50 pages) may require extended processing time
- JSON Parser v3.2 handles most academic document structures; edge cases may require configuration tuning

## Dependencies

Key Python packages:
- `httpx`: HTTP client for API calls
- `python-dotenv`: Environment variable management
- `google-generativeai`: Gemini AI integration
- `pyyaml`: YAML configuration parsing for JSON parser
- `Pillow`: Image processing (if needed)
- `fastapi`, `uvicorn`: Web framework (for future API endpoints)

All dependencies are listed in `config/requirements.md`

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