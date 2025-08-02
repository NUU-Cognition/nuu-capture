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
    
    # This regex identifies lines that should NOT be joined with a previous line.
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
        r'```'               # Code fence <<< ADDED
        r')$'
    )
    
    lines = text.split('\n')
    processed_lines = []
    paragraph_buffer = []

    for line in lines:
        stripped_line = line.strip()
        is_table_row = '|' in stripped_line

        # Check if the line is a breaker, a table row, or is blank
        if not stripped_line or breaker_line_pattern.match(stripped_line) or is_table_row:
            # If we have a paragraph in the buffer, process and add it.
            if paragraph_buffer:
                processed_lines.append(' '.join(paragraph_buffer))
                paragraph_buffer = []
            
            # Add the breaker/blank line itself.
            processed_lines.append(line)
        else:
            # This is a regular line of text, add it to our buffer.
            paragraph_buffer.append(stripped_line)

    # After the loop, add any remaining text from the buffer.
    if paragraph_buffer:
        processed_lines.append(' '.join(paragraph_buffer))

    # Join all processed lines and clean up potential excess newlines
    final_text = '\n'.join(processed_lines)
    final_text = re.sub(r'\n{3,}', '\n\n', final_text) # Collapse 3+ newlines to 2
    
    return final_text

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
               "  Input: saved_markdowns/processed_document.md\n"
               "  Output: saved_markdowns/stage1_format.md"
    )
    parser.add_argument("input_file", nargs='?', default="saved_markdowns/processed_document.md", 
                       help="The path to the raw input Markdown file. (default: saved_markdowns/processed_document.md)")
    parser.add_argument("output_file", nargs='?', default="saved_markdowns/stage1_format.md",
                       help="The path where the cleaned output file will be saved. (default: saved_markdowns/stage1_format.md)")
    
    args = parser.parse_args()

    # Ensure the output directory exists
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[*] Created output directory: {output_dir}")

    print(f"[*] Reading from: {args.input_file}")
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            raw_text = f.read()
    except FileNotFoundError:
        print(f"[!] Error: Input file not found at '{args.input_file}'", file=sys.stderr)
        print(f"[!] Please ensure the file exists or provide a different input path.", file=sys.stderr)
        sys.exit(1)

    # --- Run the processing pipeline ---
    print("[*] Applying common OCR fixes...")
    processed_text = fix_common_ocr_errors(raw_text)
    
    print("[*] Fixing paragraph formatting...")
    processed_text = fix_paragraphs(processed_text)
    # ------------------------------------

    print(f"[*] Writing cleaned output to: {args.output_file}")
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(processed_text)
        
    print("[+] Stage 1 preprocessing complete!")


if __name__ == "__main__":
    main()