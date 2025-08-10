import re
import argparse
import sys
import os

def fix_common_ocr_errors(text: str) -> str:
    """
    Applies a series of simple, common search-and-replace fixes for OCR errors.
    """
    fixes = {
        "https: //": "https://",
        # Add other common ligature or OCR mistakes here if needed
        # e.g., "ﬁ": "fi", "ﬂ": "fl"
    }
    for bad, good in fixes.items():
        text = text.replace(bad, good)
    return text

def fix_paragraphs(text: str) -> str:
    """
    The core function to fix paragraph formatting.

    It iterates through lines, identifying "breaker" lines that signal a new
    block (e.g., headings, lists, blank lines). All consecutive lines of
    regular text between these breakers are joined into a single paragraph.
    """
    breaker_line_pattern = re.compile(
        r'^\s*('
        r'#{1,6}\s'          # Headings (e.g., #, ##)
        r'\*\s'              # Unordered list item (*)
        r'-\s'               # Unordered list item (-)
        r'\d+\.\s'           # Ordered list item (1.)
        r'>'                 # Blockquote
        r'---'               # Horizontal rule
        r'==='               # Horizontal rule
        r'\!\[.*\]\(.*\)'    # Image tag
        r'\[\^.*\]:'         # Footnote definition
        r'Figure \d+:'       # Figure Captions
        r'Table \d+:'        # Table Captions
        r'```'               # Code fence
        r')$'
    )
    
    lines = text.split('\n')
    processed_lines = []
    paragraph_buffer = []

    for line in lines:
        stripped_line = line.strip()
        is_table_row = '|' in stripped_line

        if not stripped_line or breaker_line_pattern.match(stripped_line) or is_table_row:
            if paragraph_buffer:
                processed_lines.append(' '.join(paragraph_buffer))
                paragraph_buffer = []
            processed_lines.append(line)
        else:
            paragraph_buffer.append(stripped_line)

    if paragraph_buffer:
        processed_lines.append(' '.join(paragraph_buffer))

    final_text = '\n'.join(processed_lines)
    return re.sub(r'\n{3,}', '\n\n', final_text)

# <<< NEW FUNCTION to remove appendix and other content after references >>>
def truncate_after_references(text: str) -> str:
    """
    Finds the 'References' section and removes all content that follows it.
    If no 'References' section is found, it returns the original text.
    """
    # Define a pattern to find the start of the References section
    ref_pattern = r'(?m)^##\s+References'
    ref_match = re.search(ref_pattern, text)

    if not ref_match:
        # If no "References" heading is found, return the document as is.
        print("   -> 'References' section not found. No truncation performed.")
        return text

    # Get the start index of the "References" heading
    start_of_references = ref_match.start()

    # Get the text from the start of references to the end of the document
    text_after_references = text[start_of_references:]

    # Find the NEXT major heading (# or ##) after the start of the References heading
    # We search in the text *after* the first line of the new section
    next_heading_pattern = r'(?m)^#{1,2}\s'
    # Skip the first line (the References heading itself) and search for the next heading
    text_after_first_line = text_after_references.split('\n', 1)[1] if '\n' in text_after_references else ""
    next_heading_match = re.search(next_heading_pattern, text_after_first_line)

    if next_heading_match:
        # If a next heading is found, truncate the document there
        end_of_references = start_of_references + next_heading_match.start()
        print("   -> Found next major heading after 'References'. Truncating document.")
        return text[:end_of_references].strip()
    else:
        # If no heading follows, References is the last section. Keep everything.
        print("   -> 'References' is the last section. No truncation needed.")
        return text

def main():
    """
    Main function to run the preprocessing script from the command line.
    """
    parser = argparse.ArgumentParser(
        description="A script to clean and preprocess Markdown files generated from OCR.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Example Usage:\n"
               "python preprocess.py [input_file] [output_file]\n"
               "If no arguments provided, uses default paths:\n"
               "  Input: document_ocr_test/pre_stage_1.md\n"
               "  Output: document_ocr_test/stage_1_complete.md"
    )
    parser.add_argument("input_file", nargs='?', default=None, 
                       help="The path to the raw input Markdown file. (default: auto-detect from most recent folder)")
    parser.add_argument("output_file", nargs='?', default=None,
                       help="The path where the cleaned output file will be saved. (default: auto-detect from input path)")
    
    args = parser.parse_args()
    
    # Auto-detect paths if not provided
    if args.input_file is None or args.output_file is None:
        # Find most recent output directory (fallback to document_ocr_test for backward compatibility)
        possible_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and d != 'ocr_get' and d != 'ocr_fix' and d != 'txtfiles' and d != '.git']
        if possible_dirs:
            # Sort by modification time, most recent first
            possible_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            detected_dir = possible_dirs[0]
        else:
            detected_dir = "document_ocr_test"  # Fallback
        
        if args.input_file is None:
            args.input_file = f"{detected_dir}/pre_stage_1.md"
        if args.output_file is None:
            args.output_file = f"{detected_dir}/stage_1_complete.md"

    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[*] Created output directory: {output_dir}")

    print(f"[*] Reading from: {args.input_file}")
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except FileNotFoundError as e:
        print(f"[!] Error: Input file not found at '{args.input_file}'", file=sys.stderr)
        sys.exit(1)

    # --- Run the processing pipeline ---
    # <<< ADDED: New truncation step is now the FIRST step in the pipeline.
    print("[*] Truncating document to remove appendix...")
    processed_text = truncate_after_references(raw_text)

    print("[*] Applying common OCR fixes...")
    processed_text = fix_common_ocr_errors(processed_text)
    
    print("[*] Fixing paragraph formatting...")
    processed_text = fix_paragraphs(processed_text)
    # ------------------------------------

    print(f"\n[*] Writing cleaned output to: {args.output_file}")
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(processed_text)
        
    print("[+] Stage 1 preprocessing complete!")


if __name__ == "__main__":
    main()