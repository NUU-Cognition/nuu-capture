#!/usr/bin/env python3
"""
Unified OCR Pipeline Script

This script runs the complete OCR pipeline in a single command:
Stage 1: PDF Processing (process_pdf.py) - OCR extraction using Mistral API
Stage 2: Image Link Fixing (fix_markdown.py) - Fix image references
Stage 3: Preprocessing (stage1.py) - OCR fixes and truncation
Stage 4: LLM Formatting (stage2.py) - Advanced formatting with Gemini API
Stage 5: JSON Parsing (parser_v3.py) - Convert markdown to structured JSON

Usage:
    python unified_pipeline.py <pdf_input> [output_dir]
    python unified_pipeline.py test_pdf/bio_paper_1.pdf
    python unified_pipeline.py https://example.com/paper.pdf
    python unified_pipeline.py test_pdf/bio_paper_1.pdf custom_output_folder
"""

import os
import sys
import subprocess
import argparse
import time
import shutil
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from typing import Optional, List, Union, Tuple
from datetime import datetime

# Load environment variables
load_dotenv()

def log_stage(stage_name: str, message: str) -> None:
    """Print formatted log messages for each pipeline stage."""
    print(f"\n{'='*60}")
    print(f"[{stage_name}]")
    print(f"{'='*60}")
    print(f"* {message}")
    print()

def log_success(message: str) -> None:
    """Print success message."""
    print(f"+ {message}")

def log_error(message: str) -> None:
    """Print error message."""
    print(f"- {message}")

def log_info(message: str) -> None:
    """Print info message."""
    print(f"i {message}")

def run_command(command: List[str], stage_name: str) -> bool:
    """Run a command and handle errors appropriately."""
    log_info(f"Running: {' '.join(command)}")
    try:
        result = subprocess.run(
            command, 
            check=True, 
            capture_output=True, 
            text=True,
            cwd=os.getcwd()
        )
        
        # Print stdout if it exists
        if result.stdout.strip():
            print(result.stdout)
            
        log_success(f"{stage_name} completed successfully!")
        return True
        
    except subprocess.CalledProcessError as e:
        log_error(f"{stage_name} failed with return code {e.returncode}")
        if e.stdout:
            print("STDOUT:", e.stdout)
        if e.stderr:
            print("STDERR:", e.stderr)
        return False
    except Exception as e:
        log_error(f"Unexpected error in {stage_name}: {e}")
        return False

def check_requirements() -> bool:
    """Check if required API keys and dependencies are available."""
    log_stage("Environment Check", "Verifying API keys and dependencies")
    
    # Check API keys
    mistral_key = os.getenv("MISTRAL_API_KEY")
    gemini_key = os.getenv("GEMINI_API_KEY")
    
    if not mistral_key:
        log_error("MISTRAL_API_KEY not found in environment variables")
        return False
        
    if not gemini_key:
        log_error("GEMINI_API_KEY not found in environment variables")
        return False
    
    # Check if required directories exist
    required_dirs = ["stages/01_extract", "stages/02_preprocess", "stages/03_format", "json_parser", "config"]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            log_error(f"Required directory '{dir_name}' not found")
            return False

    # Check if required files exist
    required_files = [
        "stages/01_extract/process_pdf.py",
        "stages/01_extract/fix_markdown.py",
        "stages/02_preprocess/stage1.py",
        "stages/03_format/stage2.py",
        "json_parser/parser_v3.py",
        "config/universal_research_prompt.md"
    ]
    
    for file_path in required_files:
        if not os.path.exists(file_path):
            log_error(f"Required file '{file_path}' not found")
            return False
    
    log_success("Environment check passed - all requirements satisfied")
    return True

def get_pdf_name(document_input: str) -> str:
    """Extract PDF name without extension from URL or local path."""
    def is_url(string):
        try:
            result = urlparse(string)
            return all([result.scheme, result.netloc])
        except:
            return False

    if is_url(document_input):
        # Extract filename from URL
        parsed_url = urlparse(document_input)
        filename = Path(parsed_url.path).name
        if filename and filename.lower().endswith('.pdf'):
            return filename[:-4]  # Remove .pdf extension
        else:
            # Fallback to last part of path or domain
            return parsed_url.path.split('/')[-1] or parsed_url.netloc.replace('.', '_')
    else:
        # Local file path
        return Path(document_input).stem

def copy_to_standardized_outputs(output_dir: str, pdf_name: str) -> Tuple[Optional[str], Optional[str]]:
    """
    Copy final outputs to standardized testing folders.

    Args:
        output_dir: The working output directory
        pdf_name: Name of the PDF document

    Returns:
        Tuple of (json_copy_path, markdown_copy_path)
    """
    # Create timestamp for unique filenames
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Ensure standardized output directories exist
    json_output_dir = "output/json_output"
    markdown_output_dir = "output/markdown_output"
    os.makedirs(json_output_dir, exist_ok=True)
    os.makedirs(markdown_output_dir, exist_ok=True)

    json_copy_path = None
    markdown_copy_path = None

    # Copy JSON output
    json_source = os.path.join(output_dir, "final_formatted_output.json")
    if os.path.exists(json_source):
        json_copy_filename = f"{pdf_name}_{timestamp}.json"
        json_copy_path = os.path.join(json_output_dir, json_copy_filename)
        shutil.copy2(json_source, json_copy_path)
        log_success(f"JSON output copied to: {json_copy_path}")
    else:
        log_error(f"JSON source file not found: {json_source}")

    # Copy final markdown output
    markdown_source = os.path.join(output_dir, "final_formatted.md")
    if os.path.exists(markdown_source):
        markdown_copy_filename = f"{pdf_name}_{timestamp}.md"
        markdown_copy_path = os.path.join(markdown_output_dir, markdown_copy_filename)
        shutil.copy2(markdown_source, markdown_copy_path)
        log_success(f"Markdown output copied to: {markdown_copy_path}")
    else:
        log_error(f"Markdown source file not found: {markdown_source}")

    return json_copy_path, markdown_copy_path

def find_most_recent_output_dir() -> Optional[str]:
    """Find the most recently created output directory."""
    possible_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.') and d not in ['stages', 'config', 'utils', 'output', 'venv']]
    if possible_dirs:
        # Sort by modification time, most recent first
        possible_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return possible_dirs[0]
    return None

def run_pipeline(pdf_input: str, output_dir: Optional[str] = None, parser_version: str = "v3") -> Union[str, bool]:
    """Run the complete OCR pipeline."""
    
    # Stage 1: PDF Processing
    log_stage("Stage 1: PDF Processing", "Extracting content and images using Mistral OCR API")
    
    if output_dir:
        process_cmd = ["python", "stages/01_extract/process_pdf.py", pdf_input, output_dir]
    else:
        process_cmd = ["python", "stages/01_extract/process_pdf.py", pdf_input]
    
    if not run_command(process_cmd, "PDF Processing"):
        return False
    
    # Determine the actual output directory
    if output_dir:
        actual_output_dir = output_dir
    else:
        # Auto-detect based on PDF name
        pdf_name = get_pdf_name(pdf_input)
        actual_output_dir = pdf_name
    
    # Verify the output directory exists
    if not os.path.exists(actual_output_dir):
        # Try to find the most recent directory as fallback
        detected_dir = find_most_recent_output_dir()
        if detected_dir:
            actual_output_dir = detected_dir
            log_info(f"Using detected output directory: {actual_output_dir}")
        else:
            log_error(f"Output directory not found: {actual_output_dir}")
            return False
    
    # Verify document_content.md exists
    content_file = os.path.join(actual_output_dir, "document_content.md")
    if not os.path.exists(content_file):
        log_error(f"Expected output file not found: {content_file}")
        return False
    
    # Stage 2: Fix Image Links
    log_stage("Stage 2: Image Link Fixing", "Connecting image placeholders to saved image files")
    
    fix_cmd = ["python", "stages/01_extract/fix_markdown.py", actual_output_dir]
    if not run_command(fix_cmd, "Image Link Fixing"):
        return False
    
    # Stage 3: Stage 1 Preprocessing
    log_stage("Stage 3: Stage 1 Preprocessing", "Applying OCR fixes, truncation, and paragraph reconstruction")
    
    input_file = os.path.join(actual_output_dir, "pre_stage_1.md")
    output_file = os.path.join(actual_output_dir, "stage_1_complete.md")
    stage1_cmd = ["python", "stages/02_preprocess/stage1.py", input_file, output_file]
    
    if not run_command(stage1_cmd, "Stage 1 Preprocessing"):
        return False
    
    # Stage 4: Stage 2 LLM Formatting
    log_stage("Stage 4: LLM Formatting", "Applying advanced formatting using Gemini AI")

    input_file = os.path.join(actual_output_dir, "stage_1_complete.md")
    output_file = os.path.join(actual_output_dir, "final_formatted.md")
    prompt_file = "config/universal_research_prompt.md"
    stage2_cmd = ["python", "stages/03_format/stage2.py", input_file, output_file, prompt_file]

    if not run_command(stage2_cmd, "LLM Formatting"):
        return False

    # Stage 5: JSON Structure Parsing
    if parser_version == "v4":
        log_stage("Stage 5: JSON Structure Parsing (v4 - AST-based)", "Converting markdown to structured JSON using AST parsing")
        parser_script = "json_parser/parser_v4.py"
        log_info("Using parser v4 (AST-based) - 100% accurate structure detection")
    else:
        log_stage("Stage 5: JSON Structure Parsing (v3 - regex-based)", "Converting markdown to structured JSON using pattern matching")
        parser_script = "json_parser/parser_v3.py"
        log_info("Using parser v3 (regex-based) - legacy implementation")

    input_file = os.path.join(actual_output_dir, "final_formatted.md")
    # Output will be auto-generated as final_formatted_output.json
    parser_cmd = ["python", parser_script, input_file]

    if not run_command(parser_cmd, "JSON Parsing"):
        return False

    # Copy outputs to standardized testing folders
    log_stage("Output Organization", "Copying final outputs to standardized folders for testing")
    pdf_name = get_pdf_name(pdf_input)
    json_copy_path, markdown_copy_path = copy_to_standardized_outputs(actual_output_dir, pdf_name)

    # Return all paths for final summary
    return (actual_output_dir, json_copy_path, markdown_copy_path)

def main() -> None:
    """Main function to run the unified OCR pipeline."""
    
    parser = argparse.ArgumentParser(
        description="Unified OCR Pipeline - Complete PDF to formatted Markdown conversion",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python unified_pipeline.py output/test_pdf/bio_paper_1.pdf
  python unified_pipeline.py https://example.com/paper.pdf
  python unified_pipeline.py output/test_pdf/bio_paper_1.pdf custom_output_folder
  python unified_pipeline.py "output/test_pdf/354_MARPLE_A_Benchmark_for_Lon.pdf"
  python unified_pipeline.py output/test_pdf/bio_paper_1.pdf --parser-version v4

Pipeline Stages:
  1. PDF Processing       - OCR extraction using Mistral API
  2. Image Link Fixing    - Fix image references in markdown
  3. Preprocessing        - OCR fixes, truncation, paragraph reconstruction
  4. LLM Formatting       - Advanced formatting using Gemini API
  5. JSON Parsing         - Convert markdown to structured JSON
                           (v3: regex-based, v4: AST-based)

Output Files (saved in working directory):
  - document_content.md           (raw OCR output)
  - pre_stage_1.md                (after image link fixing)
  - stage_1_complete.md           (after preprocessing)
  - final_formatted.md            (final formatted markdown)
  - final_formatted_output.json   (structured JSON output)
  - img-X.jpeg                    (extracted images)

Standardized Testing Outputs:
  - output/markdown_output/<pdf>_<timestamp>.md    (final markdown copy)
  - output/json_output/<pdf>_<timestamp>.json      (final JSON copy)
        """
    )
    
    parser.add_argument(
        "pdf_input", 
        help="PDF document to process (URL or local file path)"
    )
    parser.add_argument(
        "output_dir", 
        nargs='?', 
        default=None,
        help="Output directory for processed files (default: PDF filename)"
    )
    parser.add_argument(
        "--skip-checks",
        action="store_true",
        help="Skip environment and requirements checks"
    )
    parser.add_argument(
        "--parser-version",
        choices=["v3", "v4"],
        default="v3",
        help="Parser version to use (v3=regex-based, v4=AST-based, default: v3)"
    )
    
    args = parser.parse_args()
    
    # Print banner
    print("=" + "="*60)
    print("UNIFIED OCR PIPELINE - PDF TO FORMATTED MARKDOWN")
    print("=" + "="*60)
    print(f"Input: {args.pdf_input}")
    if args.output_dir:
        print(f"Output Directory: {args.output_dir}")
    else:
        print(f"Output Directory: Auto-generated from PDF filename")
    print()
    
    start_time = time.time()
    
    try:
        # Check requirements unless skipped
        if not args.skip_checks:
            if not check_requirements():
                sys.exit(1)
        
        # Run the complete pipeline
        pipeline_result = run_pipeline(args.pdf_input, args.output_dir, args.parser_version)

        if pipeline_result:
            # Unpack results
            output_directory, json_copy_path, markdown_copy_path = pipeline_result

            end_time = time.time()
            duration = end_time - start_time

            # Final success message
            print("\n" + "="*60)
            print("PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"Output Directory: {os.path.abspath(output_directory)}")
            print(f"Total Processing Time: {duration:.2f} seconds")
            print()
            print("Generated Files:")

            # List all generated files
            files_to_check = [
                ("document_content.md", "Raw OCR output"),
                ("pre_stage_1.md", "After image link fixing"),
                ("stage_1_complete.md", "After preprocessing"),
                ("final_formatted.md", "Final formatted markdown"),
                ("final_formatted_output.json", "Structured JSON output")
            ]

            for filename, description in files_to_check:
                file_path = os.path.join(output_directory, filename)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"   + {filename:20} - {description} ({file_size:,} bytes)")
                else:
                    print(f"   - {filename:20} - Missing!")

            # Count images
            image_files = [f for f in os.listdir(output_directory) if f.startswith('img-') and any(f.endswith(ext) for ext in ['.jpeg', '.jpg', '.png', '.gif'])]
            if image_files:
                print(f"   + {len(image_files)} extracted images")

            print(f"\n[*] Working Directory Outputs:")
            print(f"    Markdown: {os.path.abspath(os.path.join(output_directory, 'final_formatted.md'))}")
            print(f"    JSON:     {os.path.abspath(os.path.join(output_directory, 'final_formatted_output.json'))}")

            print(f"\n[*] Standardized Testing Outputs:")
            if markdown_copy_path:
                print(f"    Markdown: {os.path.abspath(markdown_copy_path)}")
            else:
                print(f"    Markdown: Failed to copy")

            if json_copy_path:
                print(f"    JSON:     {os.path.abspath(json_copy_path)}")
            else:
                print(f"    JSON:     Failed to copy")
            
        else:
            log_error("Pipeline failed. Please check the error messages above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\nPipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()