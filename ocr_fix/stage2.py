import re
import argparse
import sys
import os
import time
import google.generativeai as genai
from google.api_core import exceptions
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# --- LLM Configuration ---
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    print("+ Gemini API configured successfully")
except Exception as e:
    print(f"- Error configuring Gemini API: {e}")
    sys.exit(1)


# <<< MODIFIED: The MASTER_PROMPT variable has been removed from here.

def split_into_sections(markdown_text: str) -> list[str]:
    """
    Splits the markdown document into sections based on Level 1 or 2 headings.
    This allows us to process the document chunk by chunk.
    """
    sections = re.split(r'(?m)^#{1,2}\s', markdown_text)
    processed_sections = []
    if sections[0].strip():
        processed_sections.append(sections[0])
    headings = re.findall(r'(?m)^#{1,2}\s.*', markdown_text)
    for i, section_content in enumerate(sections[1:]):
        if i < len(headings):
            full_section = headings[i] + '\n' + section_content
            processed_sections.append(full_section)
    return processed_sections if processed_sections else [markdown_text]


# <<< MODIFIED: Function now accepts the prompt_template as an argument.
def call_llm_for_correction(text_chunk: str, prompt_template: str, model) -> str | None:
    """
    Sends a chunk of text to the LLM with the master prompt and returns the corrected version.
    Returns None if the API call fails.
    """
    prompt = prompt_template.format(text_chunk=text_chunk)
    try:
        response = model.generate_content(prompt)
        if not response.text.strip():
            print("\n[!] Warning: LLM returned an empty response.")
            return None
        return response.text.strip()
    except Exception as e:
        print(f"\n[!] Error during LLM call: {e}")
        return None


def main():
    """
    Main function to run the Stage 2 processing.
    """
    parser = argparse.ArgumentParser(
        description="Stage 2: Applies LLM-based formatting to a preprocessed Markdown file.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Example Usage:\n"
               "python stage2.py [input_file] [output_file] [prompt_file]\n"
               "If no arguments provided, uses default paths."
    )
    # <<< MODIFIED: Added an argument for the prompt file path.
    parser.add_argument("input_file", nargs='?', default=None, 
                       help="The path to the Stage 1 preprocessed file. (default: auto-detect from most recent folder)")
    parser.add_argument("output_file", nargs='?', default=None,
                       help="The path where the final, fully formatted file will be saved. (default: auto-detect from input path)")
    parser.add_argument("prompt_file", nargs='?', default="txtfiles/universal_research_prompt.txt",
                       help="The path to the .txt file containing the formatting prompt.")
    
    args = parser.parse_args()
    
    # Auto-detect paths if not provided
    if args.input_file is None or args.output_file is None:
        # Find most recent output directory (fallback to document_ocr_test for backward compatibility)
        possible_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.') and d not in ['ocr_get', 'ocr_fix', 'txtfiles', 'venv', 'example_format_md', 'test_pdf']]
        if possible_dirs:
            # Sort by modification time, most recent first
            possible_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            detected_dir = possible_dirs[0]
        else:
            detected_dir = "document_ocr_test"  # Fallback
        
        if args.input_file is None:
            args.input_file = f"{detected_dir}/stage_1_complete.md"
        if args.output_file is None:
            args.output_file = f"{detected_dir}/final_formatted.md"

    # Resolve paths to absolute paths
    from pathlib import Path
    args.input_file = str(Path(args.input_file).resolve())
    args.output_file = str(Path(args.output_file).resolve())
    args.prompt_file = str(Path(args.prompt_file).resolve())

    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[*] Created output directory: {output_dir}")

    # Load input files
    print(f"[*] Reading Stage 1 file from: {args.input_file}")
    
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            stage1_text = f.read()
        
        print(f"[*] Reading Universal Research Prompt from: {args.prompt_file}")
        with open(args.prompt_file, 'r', encoding='utf-8') as f:
            prompt_text = f.read()
            
    except FileNotFoundError as e:
        print(f"[!] Error: An input file was not found.", file=sys.stderr)
        print(f"    Details: {e}", file=sys.stderr)
        sys.exit(1)

    print("[*] Splitting document into logical sections...")
    sections = split_into_sections(stage1_text)
    print(f"[*] Found {len(sections)} sections to process.")
    
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    def process_section_with_retries(section, prompt_text, section_num, pass_name=""):
        """Process a section with retry logic."""
        max_retries = 3
        corrected_chunk = None
        for attempt in range(max_retries):
            corrected_chunk = call_llm_for_correction(section, prompt_text, model)
            if corrected_chunk and corrected_chunk.strip():  # Check for actual content
                print(f"[*] Section {section_num}{pass_name} processed successfully.")
                return corrected_chunk
            elif corrected_chunk:
                print(f"[!] Section {section_num}{pass_name} returned only whitespace on attempt {attempt + 1}")
            
            delay = 5 * (2 ** attempt)
            print(f"[*] Attempt {attempt + 1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)
        
        print(f"[!] FAILED to process section {section_num}{pass_name} after {max_retries} attempts.")
        return None

    try:
        # Process all sections with the universal prompt
        final_sections = []
        
        for i, section in enumerate(sections):
            heading_line = section.strip().split('\n', 1)[0]
            print(f"\n[*] Processing Section {i+1}/{len(sections)}: '{heading_line[:60]}...'")
            
            corrected_chunk = process_section_with_retries(section, prompt_text, i+1)
            final_sections.append(corrected_chunk if corrected_chunk else section)
            
        sections_to_write = final_sections

        # Create the output file first to ensure it exists
        print(f"[*] Creating output file: {args.output_file}")
        try:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write("")  # Create empty file
            print(f"[*] Output file created successfully")
        except Exception as e:
            print(f"[!] Error creating output file: {e}")
            raise

        # Write final results to file
        print(f"[*] Writing content to: {args.output_file}")
        with open(args.output_file, 'w', encoding='utf-8') as output_file:
            for i, section in enumerate(sections_to_write):
                try:
                    if section and section.strip():  # Check if section has actual content
                        output_file.write(section)
                    else:
                        print(f"[!] Warning: Section {i+1} is empty or contains only whitespace, using original...")
                        # Fall back to original section
                        if i < len(sections):
                            output_file.write(sections[i])
                        else:
                            print(f"[!] Error: No original section available for section {i+1}")
                            continue
                    
                    # Add section separator (but not after the last section)
                    if i < len(sections_to_write) - 1:
                        output_file.write("\n\n")
                        
                except Exception as e:
                    print(f"[!] Error writing section {i+1}: {e}")
                    print(f"[!] Section content type: {type(section)}, length: {len(section) if section else 'None'}")
                    # Try to write original section as fallback
                    if i < len(sections):
                        output_file.write(sections[i])
                        if i < len(sections_to_write) - 1:
                            output_file.write("\n\n")
        
        print("\n[+] Stage 2 processing complete! Your document is fully formatted.")
        print(f"[*] Final output saved to: {args.output_file}")

    except Exception as e:
        print(f"\n[!] An error occurred while writing to the file: {e}")

if __name__ == "__main__":
    main()