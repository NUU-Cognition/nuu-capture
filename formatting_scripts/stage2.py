import re
import argparse
import sys
import os
import time
import google.generativeai as genai
from google.api_core import exceptions

# --- LLM Configuration ---
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    print("✅ Gemini API configured successfully")
except Exception as e:
    print(f"❌ Error configuring Gemini API: {e}")
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
    parser.add_argument("input_file", nargs='?', default="saved_markdowns/stage1_format.md", 
                       help="The path to the Stage 1 preprocessed file.")
    parser.add_argument("output_file", nargs='?', default="saved_markdowns/stage2_format.md",
                       help="The path where the final, fully formatted file will be saved.")
    parser.add_argument("prompt_file", nargs='?', default="txtfiles/formatting_prompt.txt",
                       help="The path to the .txt file containing the master prompt.")
    
    args = parser.parse_args()

    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[*] Created output directory: {output_dir}")

    # <<< MODIFIED: Reads all three files at the start.
    print(f"[*] Reading Stage 1 file from: {args.input_file}")
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            stage1_text = f.read()
        print(f"[*] Reading Master Prompt from: {args.prompt_file}")
        with open(args.prompt_file, 'r', encoding='utf-8') as f:
            master_prompt_text = f.read()
    except FileNotFoundError as e:
        print(f"[!] Error: An input file was not found.", file=sys.stderr)
        print(f"    Details: {e}", file=sys.stderr)
        sys.exit(1)

    print("[*] Splitting document into logical sections...")
    sections = split_into_sections(stage1_text)
    print(f"[*] Found {len(sections)} sections to process.")
    
    model = genai.GenerativeModel('gemini-1.5-pro-latest')

    try:
        with open(args.output_file, 'w', encoding='utf-8') as output_file:
            for i, section in enumerate(sections):
                heading_line = section.strip().split('\n', 1)[0]
                print(f"\n[*] Processing Section {i+1}/{len(sections)}: '{heading_line[:60]}...'")
                
                max_retries = 3
                corrected_chunk = None
                for attempt in range(max_retries):
                    # <<< MODIFIED: Pass the loaded master_prompt_text to the function.
                    corrected_chunk = call_llm_for_correction(section, master_prompt_text, model)
                    if corrected_chunk:
                        print(f"[*] Section {i+1} processed successfully.")
                        break
                    
                    delay = 5 * (2 ** attempt)
                    print(f"[*] Attempt {attempt + 1} failed. Retrying in {delay} seconds...")
                    time.sleep(delay)
                
                if corrected_chunk:
                    output_file.write(corrected_chunk)
                else:
                    print(f"[!] FAILED to process section {i+1} after {max_retries} attempts. Writing original content to prevent data loss.")
                    output_file.write(section)
                
                if i < len(sections) - 1:
                    output_file.write("\n\n")
        
        print("\n[+] Stage 2 processing complete! Your document is fully formatted.")
        print(f"[*] Final output saved to: {args.output_file}")

    except Exception as e:
        print(f"\n[!] An error occurred while writing to the file: {e}")

if __name__ == "__main__":
    main()