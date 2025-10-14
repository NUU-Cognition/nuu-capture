# Standardized Output Structure for Testing

## Overview

This document describes the standardized output folder structure created for systematic testing and continuous integration of pipeline improvements.

---

## Folder Structure

```
output/
├── json_output/         # Standardized JSON outputs for testing
│   └── <document>_<timestamp>.json
├── markdown_output/     # Standardized markdown outputs for testing
│   └── <document>_<timestamp>.md
├── test_pdf/           # Test PDF documents
└── example_format_md/  # Example markdown formats
```

---

## Purpose

### **Why Standardized Outputs?**

1. **Continuous Testing**: As pipeline changes are made, outputs can be continuously compared
2. **Quality Assurance**: Easy to verify improvements don't break existing functionality
3. **Regression Testing**: Compare new outputs with previous versions
4. **Benchmarking**: Measure improvements in parsing accuracy and formatting quality
5. **Version Control Friendly**: Timestamped files allow tracking changes over time

---

## Output Locations

### **1. Working Directory Outputs** (per-document)

Each processed document creates a working directory with all intermediate files:

```
<document_name>/
├── document_content.md           # Raw OCR output
├── pre_stage_1.md                # After image link fixing
├── stage_1_complete.md           # After preprocessing
├── final_formatted.md            # Final formatted markdown
├── final_formatted_output.json   # Structured JSON output
└── img-*.jpeg                    # Extracted images
```

**Purpose**: Complete processing artifacts for debugging and analysis

---

### **2. Standardized Testing Outputs** (centralized)

Final outputs are also copied to standardized folders:

```
output/json_output/
└── <document>_20251014_153045.json

output/markdown_output/
└── <document>_20251014_153045.md
```

**Naming Convention**: `<document_name>_<YYYYMMDD_HHMMSS>.<ext>`

**Purpose**: Centralized location for testing and comparison

---

## File Naming

### **Format**

```
<document_name>_<timestamp>.<extension>

Examples:
- bio_paper_1_20251014_153045.md
- academic_paper_20251014_153045.json
- research_doc_20251014_153045.md
```

### **Components**

- **document_name**: Extracted from PDF filename or input path
- **timestamp**: `YYYYMMDD_HHMMSS` format for unique identification
- **extension**: `.md` for markdown, `.json` for structured data

---

## Usage

### **Unified Pipeline** (Recommended)

The unified pipeline automatically saves outputs to both locations:

```bash
python unified_pipeline.py output/test_pdf/document.pdf
```

**Output**:
```
Working Directory: document/
  - All intermediate files
  - Final outputs (final_formatted.md, final_formatted_output.json)

Standardized Testing:
  - output/markdown_output/document_20251014_153045.md
  - output/json_output/document_20251014_153045.json
```

---

### **Stage 2 (LLM Formatting) Standalone**

When running stage2.py directly, it also saves to standardized folder:

```bash
python stages/03_format/stage2.py input.md output.md
```

**Output**:
```
Working Directory:
  - output.md (specified location)

Standardized Testing:
  - output/markdown_output/<doc>_<timestamp>.md
```

---

## Testing Workflow

### **1. Baseline Creation**

Run pipeline on test documents to create baseline outputs:

```bash
python unified_pipeline.py output/test_pdf/test_doc1.pdf
python unified_pipeline.py output/test_pdf/test_doc2.pdf
python unified_pipeline.py output/test_pdf/test_doc3.pdf
```

**Result**: Baseline files in `output/json_output/` and `output/markdown_output/`

---

### **2. Make Changes**

Modify pipeline code (e.g., improve parser, update prompt):

```bash
# Edit json_parser/parser_v3.py
# Or edit config/universal_research_prompt.md
```

---

### **3. Re-run Pipeline**

Process same documents again:

```bash
python unified_pipeline.py output/test_pdf/test_doc1.pdf
```

**Result**: New timestamped files in standardized folders

---

### **4. Compare Outputs**

Compare new outputs with baseline:

```bash
# Compare JSON structure
diff output/json_output/test_doc1_20251014_100000.json \
     output/json_output/test_doc1_20251014_153045.json

# Compare markdown formatting
diff output/markdown_output/test_doc1_20251014_100000.md \
     output/markdown_output/test_doc1_20251014_153045.md
```

---

## Integration with Version Control

### **.gitignore Recommendations**

```gitignore
# Working directories (document-specific outputs)
/*_output/
document_*/
bio_paper_*/
academic_paper_*/

# Keep standardized outputs for reference (optional)
# Uncomment to exclude from version control:
# output/json_output/*.json
# output/markdown_output/*.md

# Keep a few reference outputs for testing
!output/json_output/reference_*.json
!output/markdown_output/reference_*.md
```

**Strategy Options**:

1. **Track Reference Outputs**: Commit a few "golden" outputs for CI/CD comparison
2. **Exclude All Outputs**: Keep outputs local, compare manually
3. **Track Changes**: Commit outputs when making major improvements

---

## Comparison Tools

### **JSON Comparison**

```bash
# Pretty-print and diff
python -m json.tool output/json_output/doc1_old.json > old.json
python -m json.tool output/json_output/doc1_new.json > new.json
diff old.json new.json

# Use jq for advanced comparison
jq '.document_structure.elements | length' output/json_output/doc1_old.json
jq '.document_structure.elements | length' output/json_output/doc1_new.json
```

### **Markdown Comparison**

```bash
# Side-by-side comparison
diff -y output/markdown_output/doc1_old.md output/markdown_output/doc1_new.md | less

# Word count comparison
wc -w output/markdown_output/doc1_old.md output/markdown_output/doc1_new.md

# Count heading levels
grep -c "^#" output/markdown_output/doc1_old.md
grep -c "^##" output/markdown_output/doc1_old.md
```

---

## Automated Testing Script

### **Example: Compare All Outputs**

```bash
#!/bin/bash
# test_regression.sh

BASELINE_DIR="output/json_output/baseline"
NEW_DIR="output/json_output"

for baseline in $BASELINE_DIR/*.json; do
    filename=$(basename "$baseline")
    new_file="$NEW_DIR/$filename"

    if [ -f "$new_file" ]; then
        echo "Comparing: $filename"
        diff <(jq -S . "$baseline") <(jq -S . "$new_file") > /dev/null
        if [ $? -eq 0 ]; then
            echo "  ✓ No changes"
        else
            echo "  ✗ Differences found"
            diff <(jq -S . "$baseline") <(jq -S . "$new_file") | head -20
        fi
    else
        echo "Missing: $filename"
    fi
    echo
done
```

---

## Benefits Summary

### **For Development**

- ✅ **Easy Comparison**: Compare before/after improvements
- ✅ **Version Tracking**: Timestamped outputs track evolution
- ✅ **Regression Detection**: Quickly spot unintended changes
- ✅ **Benchmarking**: Measure improvements objectively

### **For Testing**

- ✅ **Centralized Location**: All test outputs in one place
- ✅ **Organized**: Separate JSON and markdown outputs
- ✅ **Repeatable**: Re-run same tests easily
- ✅ **Traceable**: Timestamps show when processed

### **For Quality Assurance**

- ✅ **Verification**: Ensure changes improve outputs
- ✅ **Documentation**: Outputs serve as test artifacts
- ✅ **CI/CD Integration**: Easy to automate comparisons
- ✅ **Debugging**: Reference outputs help identify issues

---

## Maintenance

### **Cleaning Old Outputs**

Remove old timestamped files periodically:

```bash
# Keep only last 10 outputs per document
cd output/json_output
ls -t bio_paper_1_*.json | tail -n +11 | xargs rm

cd ../markdown_output
ls -t bio_paper_1_*.md | tail -n +11 | xargs rm
```

### **Archiving Baseline Outputs**

Create "golden" reference outputs:

```bash
# Copy important baselines
mkdir -p output/json_output/baseline
cp output/json_output/test_doc1_20251014_153045.json \
   output/json_output/baseline/test_doc1_baseline.json
```

---

## Integration with Unified Pipeline

### **How It Works**

1. **Pipeline Completes**: All 5 stages run successfully
2. **JSON Generated**: `final_formatted_output.json` created in working directory
3. **Markdown Generated**: `final_formatted.md` created in working directory
4. **Automatic Copy**: Outputs copied to standardized folders with timestamps
5. **Summary Displayed**: Both working directory and standardized paths shown

### **Example Output**

```
============================================================
PIPELINE COMPLETED SUCCESSFULLY!
============================================================
Output Directory: /path/to/document/
Total Processing Time: 45.23 seconds

Generated Files:
   + document_content.md    - Raw OCR output (125,430 bytes)
   + pre_stage_1.md         - After image link fixing (126,890 bytes)
   + stage_1_complete.md    - After preprocessing (115,670 bytes)
   + final_formatted.md     - Final formatted markdown (118,320 bytes)
   + final_formatted_output.json - Structured JSON output (45,230 bytes)
   + 8 extracted images

[*] Working Directory Outputs:
    Markdown: /path/to/document/final_formatted.md
    JSON:     /path/to/document/final_formatted_output.json

[*] Standardized Testing Outputs:
    Markdown: /path/to/output/markdown_output/document_20251014_153045.md
    JSON:     /path/to/output/json_output/document_20251014_153045.json
```

---

## Future Enhancements

### **Planned Improvements**

1. **Automated Comparison Tool**
   - Script to compare outputs automatically
   - Generate diff reports
   - Highlight regressions

2. **CI/CD Integration**
   - GitHub Actions workflow
   - Automatic regression testing
   - Diff visualization

3. **Metrics Dashboard**
   - Track parsing accuracy over time
   - Visualize improvements
   - Element type distribution

4. **Golden Dataset**
   - Curated reference outputs
   - Known-good baselines
   - Test case library

---

## Related Documentation

- **CLAUDE.md**: Main project documentation
- **unified_pipeline.py**: Pipeline implementation
- **stages/03_format/PHASE2_IMPROVEMENTS.md**: Stage 2 improvements
- **json_parser/input-json-rule.md**: JSON output schema

---

**Document Version**: 1.0
**Date**: 2025-10-14
**Status**: Implemented and Active
