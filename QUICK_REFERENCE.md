# Quick Reference Guide

## 🚀 Single Command - Full Pipeline

```bash
python unified_pipeline.py path/to/document.pdf
```

**What it does:**
1. Extracts text and images from PDF (Mistral OCR)
2. Fixes image references in markdown
3. Cleans and preprocesses OCR output
4. Applies advanced formatting (Gemini AI)
5. Converts to structured JSON

**Output:** Everything saved in auto-generated folder named after your PDF

---

## 📁 File Structure Overview

```
ocr_script_own/
├── unified_pipeline.py              # ← RUN THIS
├── json_parser/
│   ├── parser_v3.py                 # JSON converter (Stage 5)
│   └── input-json-rule.md           # JSON schema spec
├── stages/
│   ├── 01_extract/
│   │   ├── process_pdf.py           # Stage 1: PDF → Markdown
│   │   └── fix_markdown.py          # Stage 2: Fix images
│   ├── 02_preprocess/
│   │   └── stage1.py                # Stage 3: Clean OCR
│   └── 03_format/
│       └── stage2.py                # Stage 4: LLM format
└── config/
    └── universal_research_prompt.md # Formatting instructions
```

---

## 📊 Example Workflow

```bash
# Process a local PDF
python unified_pipeline.py research_paper.pdf

# Process from URL
python unified_pipeline.py https://arxiv.org/pdf/2301.00001.pdf

# Custom output directory
python unified_pipeline.py paper.pdf my_custom_output/
```

**Output Files:**
```
research_paper/
├── final_formatted.md                # ← Your formatted markdown
├── final_formatted_output.json       # ← Your structured JSON
├── stage_1_complete.md              # Intermediate file
├── pre_stage_1.md                   # Intermediate file
├── document_content.md              # Intermediate file
└── img-0.jpeg, img-1.jpeg...        # Extracted images
```

---

## 🔧 Individual Stage Commands

If you need to run stages separately:

```bash
# Stage 1: PDF Processing
python stages/01_extract/process_pdf.py input.pdf

# Stage 2: Fix Image Links
python stages/01_extract/fix_markdown.py output_folder/

# Stage 3: Preprocessing
python stages/02_preprocess/stage1.py input.md output.md

# Stage 4: LLM Formatting
python stages/03_format/stage2.py input.md output.md config/universal_research_prompt.md

# Stage 5: JSON Parsing
python json_parser/parser_v3.py input.md
# Creates: input_output.json automatically
```

---

## 🎯 Parser Features

**Automatic Output Naming:**
- `document.md` → `document_output.json`
- `research_paper.md` → `research_paper_output.json`
- `path/to/file.md` → `path/to/file_output.json`

**Custom Output:**
```bash
python json_parser/parser_v3.py input.md -o custom_name.json
```

**Element Types in JSON:**
- `title`, `authors`, `heading`, `paragraph`, `list`
- `image`, `table`, `latex`, `references`

---

## 🔑 Environment Setup

**Required API Keys (.env file):**
```bash
MISTRAL_API_KEY=your_mistral_api_key_here
GEMINI_API_KEY=your_gemini_api_key_here
```

**Install Dependencies:**
```bash
pip install -r config/requirements.md
```

---

## ⚡ Pro Tips

1. **Check requirements first:**
   ```bash
   python unified_pipeline.py input.pdf
   # Pipeline checks API keys and files automatically
   ```

2. **Skip checks (faster):**
   ```bash
   python unified_pipeline.py input.pdf --skip-checks
   ```

3. **Process multiple papers:**
   ```bash
   for pdf in *.pdf; do
       python unified_pipeline.py "$pdf"
   done
   ```

4. **Just parse markdown to JSON:**
   ```bash
   python json_parser/parser_v3.py existing_document.md
   ```

---

## 📋 Troubleshooting

**Pipeline fails?**
- Check API keys in `.env` file
- Verify internet connection (for API calls)
- Check Python version (3.8+)

**Parser fails?**
- Ensure input is valid markdown file
- Check file path is correct
- Try with `-o` flag to specify output location

**Missing output files?**
- Check the auto-generated output directory
- Look for error messages in console
- Verify all dependencies installed

---

## 📞 Quick Help

```bash
python unified_pipeline.py --help
python json_parser/parser_v3.py --help
```

For detailed documentation, see: `CLAUDE.md`, `input-json-rule.md`
