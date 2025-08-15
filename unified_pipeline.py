#!/usr/bin/env python3
"""
Unified OCR Pipeline Script

This script runs the complete OCR pipeline in a single command:
1. PDF Processing (process_pdf.py) - OCR extraction using Mistral API
2. Image Link Fixing (fix_markdown.py) - Fix image references 
3. Stage 1 Processing (stage1.py) - OCR fixes and truncation
4. Stage 2 Processing (stage2.py) - LLM-based formatting with Gemini API

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
from pathlib import Path
from urllib.parse import urlparse
from dotenv import load_dotenv
from typing import Optional, List, Union, Tuple

# Load environment variables
load_dotenv()

def log_stage(stage_name: str, message: str) -> None:
    """Print formatted log messages for each pipeline stage."""
    print(f"\n{'='*60}")
    print(f"🔄 {stage_name}")
    print(f"{'='*60}")
    print(f"📝 {message}")
    print()

def log_success(message: str) -> None:
    """Print success message."""
    print(f"✅ {message}")

def log_error(message: str) -> None:
    """Print error message."""
    print(f"❌ {message}")

def log_info(message: str) -> None:
    """Print info message."""
    print(f"ℹ️  {message}")

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
    required_dirs = ["ocr_get", "ocr_fix", "txtfiles"]
    for dir_name in required_dirs:
        if not os.path.exists(dir_name):
            log_error(f"Required directory '{dir_name}' not found")
            return False
    
    # Check if required files exist
    required_files = [
        "ocr_get/process_pdf.py",
        "ocr_fix/fix_markdown.py", 
        "ocr_fix/stage1.py",
        "ocr_fix/stage2.py",
        "txtfiles/universal_research_prompt.txt"
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

def find_most_recent_output_dir() -> Optional[str]:
    """Find the most recently created output directory."""
    possible_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.') and d not in ['ocr_get', 'ocr_fix', 'txtfiles', 'venv', 'example_format_md', 'test_pdf']]
    if possible_dirs:
        # Sort by modification time, most recent first
        possible_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
        return possible_dirs[0]
    return None

def run_pipeline(pdf_input: str, output_dir: Optional[str] = None) -> Union[str, bool]:
    """Run the complete OCR pipeline."""
    
    # Stage 1: PDF Processing
    log_stage("Stage 1: PDF Processing", "Extracting content and images using Mistral OCR API")
    
    if output_dir:
        process_cmd = ["python", "ocr_get/process_pdf.py", pdf_input, output_dir]
    else:
        process_cmd = ["python", "ocr_get/process_pdf.py", pdf_input]
    
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
    
    fix_cmd = ["python", "ocr_fix/fix_markdown.py", actual_output_dir]
    if not run_command(fix_cmd, "Image Link Fixing"):
        return False
    
    # Stage 3: Stage 1 Preprocessing
    log_stage("Stage 3: Stage 1 Preprocessing", "Applying OCR fixes, truncation, and paragraph reconstruction")
    
    input_file = os.path.join(actual_output_dir, "pre_stage_1.md")
    output_file = os.path.join(actual_output_dir, "stage_1_complete.md")
    stage1_cmd = ["python", "ocr_fix/stage1.py", input_file, output_file]
    
    if not run_command(stage1_cmd, "Stage 1 Preprocessing"):
        return False
    
    # Stage 4: Stage 2 LLM Formatting
    log_stage("Stage 4: Stage 2 LLM Formatting", "Applying advanced formatting using Gemini AI")
    
    input_file = os.path.join(actual_output_dir, "stage_1_complete.md")
    output_file = os.path.join(actual_output_dir, "final_formatted.md")
    prompt_file = "txtfiles/universal_research_prompt.txt"
    stage2_cmd = ["python", "ocr_fix/stage2.py", input_file, output_file, prompt_file]
    
    if not run_command(stage2_cmd, "Stage 2 LLM Formatting"):
        return False
    
    return actual_output_dir

def main() -> None:
    """Main function to run the unified OCR pipeline."""
    
    parser = argparse.ArgumentParser(
        description="Unified OCR Pipeline - Complete PDF to formatted Markdown conversion",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="""
Examples:
  python unified_pipeline.py test_pdf/bio_paper_1.pdf
  python unified_pipeline.py https://example.com/paper.pdf
  python unified_pipeline.py test_pdf/bio_paper_1.pdf custom_output_folder
  python unified_pipeline.py "test_pdf/354_MARPLE_A_Benchmark_for_Lon.pdf"

Pipeline Stages:
  1. PDF Processing    - OCR extraction using Mistral API
  2. Image Link Fixing - Fix image references in markdown
  3. Stage 1 Processing - OCR fixes, truncation, paragraph reconstruction
  4. Stage 2 Processing - LLM-based formatting using Gemini API

Output Files (saved in output directory):
  - document_content.md   (raw OCR output)
  - pre_stage_1.md        (after image link fixing)
  - stage_1_complete.md   (after preprocessing)
  - final_formatted.md    (final formatted output)
  - page_X_image_Y.ext    (extracted images)
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
    
    args = parser.parse_args()
    
    # Print banner
    print("🚀 " + "="*60)
    print("🚀 UNIFIED OCR PIPELINE - PDF TO FORMATTED MARKDOWN")
    print("🚀 " + "="*60)
    print(f"📄 Input: {args.pdf_input}")
    if args.output_dir:
        print(f"📁 Output Directory: {args.output_dir}")
    else:
        print(f"📁 Output Directory: Auto-generated from PDF filename")
    print()
    
    start_time = time.time()
    
    try:
        # Check requirements unless skipped
        if not args.skip_checks:
            if not check_requirements():
                sys.exit(1)
        
        # Run the complete pipeline
        output_directory = run_pipeline(args.pdf_input, args.output_dir)
        
        if output_directory:
            end_time = time.time()
            duration = end_time - start_time
            
            # Final success message
            print("\n" + "="*60)
            print("🎉 PIPELINE COMPLETED SUCCESSFULLY!")
            print("="*60)
            print(f"📁 Output Directory: {os.path.abspath(output_directory)}")
            print(f"⏱️  Total Processing Time: {duration:.2f} seconds")
            print()
            print("📋 Generated Files:")
            
            # List all generated files
            files_to_check = [
                ("document_content.md", "Raw OCR output"),
                ("pre_stage_1.md", "After image link fixing"),
                ("stage_1_complete.md", "After preprocessing"), 
                ("final_formatted.md", "Final formatted output")
            ]
            
            for filename, description in files_to_check:
                file_path = os.path.join(output_directory, filename)
                if os.path.exists(file_path):
                    file_size = os.path.getsize(file_path)
                    print(f"   ✅ {filename:20} - {description} ({file_size:,} bytes)")
                else:
                    print(f"   ❌ {filename:20} - Missing!")
            
            # Count images
            image_files = [f for f in os.listdir(output_directory) if f.startswith('page_') and any(f.endswith(ext) for ext in ['.jpeg', '.jpg', '.png', '.gif'])]
            if image_files:
                print(f"   🖼️  {len(image_files)} extracted images")
            
            print(f"\n🎯 Your formatted document is ready: {os.path.abspath(os.path.join(output_directory, 'final_formatted.md'))}")
            
        else:
            log_error("Pipeline failed. Please check the error messages above.")
            sys.exit(1)
            
    except KeyboardInterrupt:
        print("\n\n⚠️ Pipeline interrupted by user")
        sys.exit(1)
    except Exception as e:
        log_error(f"Unexpected error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()