import re
import argparse
import sys
import os
import google.generativeai as genai

# --- LLM Configuration and Master Prompt ---

# IMPORTANT: Set up your API key.
# It's best practice to set this as an environment variable for security.
# For example: export GOOGLE_API_KEY="YOUR_API_KEY"
# The script will then automatically find it.
try:
    genai.configure(api_key=os.environ["GOOGLE_API_KEY"])
except KeyError:
    print("\n[!] Error: GOOGLE_API_KEY environment variable not set.")
    print("[!] Please set your API key to run this script.")
    sys.exit(1)


# The final, safety-focused Master Prompt we designed.
MASTER_PROMPT = """
You are an expert technical editor and Markdown formatter for academic papers. Your goal is to holistically reformat the provided Markdown section by meticulously applying the following universal rules.

**--- The Core Principle: Zero Information Loss ---**

**Your absolute highest priority is to preserve 100% of the original information.** You must not add, remove, or rephrase any scientific content, data, or wording. Reformatting should never alter the meaning. **If applying any rule below is ambiguous or risks changing the informational content of the text, you must leave that specific part in its original state.** Be conservative.

**--- Formatting & Style Rules ---**

1.  **Subheading Creation:** If a paragraph clearly begins with a topic keyword followed by a period (e.g., "Overview.", "Problem Formulation."), elevate that keyword into a Level 3 Markdown heading (`### Overview`) and remove the original keyword and period from the paragraph.

2.  **Topic Bolding:** In sections like an Appendix, if a paragraph begins with a topic keyword (e.g., "Missions."), apply bolding to that keyword (`**Missions.**`) and leave it as part of the paragraph. Use your judgment to distinguish between when a heading or bolding is more appropriate for the document's structure.

3.  **Figure Caption Formatting:**
    * A line starting with "Figure X:" is a figure caption.
    * The label must be bolded (e.g., `**Figure 1:**`).
    * The caption **must** be placed on the very next line after the Markdown image link (`![...](...)`), with **no blank line** between them.

4.  **Table Caption Formatting:**
    * A line starting with "Table X:" is a table caption.
    * The label must be bolded (e.g., `**Table 1:**`).
    * The caption **must** be placed as a separate paragraph immediately *before* the Markdown table it describes.

5.  **List Formatting:** If a paragraph contains a list written as a single line of run-on text (e.g., "..._1. First item; 2. Second item..._"), reformat it into a proper multi-line Markdown list. Preserve the exact wording of each item.

**--- Structural & Content Rules (Apply with Caution) ---**

1.  **Sentence & Paragraph Coherence:** Carefully analyze the text for grammatical flow. If you identify a sentence that is broken across different paragraphs or misplaced, reconstruct the paragraphs. **Your goal is to re-order the original text fragments correctly, NOT to rewrite or rephrase them.** The exact original wording must be preserved.

2.  **LaTeX Repair:** Find and correct any garbled or broken LaTeX formulas. **Only correct formulas where the intended mathematical expression is obvious from the corrupted text. Do not guess, invent, or simplify mathematical content.** If the intended formula is unclear, leave it as is.

**--- Final Instructions ---**

* Apply these rules comprehensively, with the Core Principle of Zero Information Loss overriding all others.
* Return ONLY the fully corrected, clean Markdown for the provided section.

Here is the text section to fix:
---
{text_chunk}
---
"""

def split_into_sections(markdown_text: str) -> list[str]:
    """
    Splits the markdown document into sections based on Level 1 or 2 headings.
    This allows us to process the document chunk by chunk.
    """
    # Split by lines starting with # or ##, but keep the delimiter (the heading).
    # The `(?=...)` is a positive lookahead that finds the position without consuming the delimiter.
    sections = re.split(r'(?m)^#{1,2}\s', markdown_text)
    
    # The first element might be empty or be the content before the first heading.
    processed_sections = []
    if sections[0].strip():
        # Handle content before the first heading (like the title block)
        processed_sections.append(sections[0])
    
    # Re-attach the headings to their respective sections
    headings = re.findall(r'(?m)^#{1,2}\s.*', markdown_text)
    
    for i, section_content in enumerate(sections[1:]):
        if i < len(headings):
            # Prepend the heading to its content
            full_section = headings[i] + '\n' + section_content
            processed_sections.append(full_section)

    return processed_sections if processed_sections else [markdown_text]


def call_llm_for_correction(text_chunk: str) -> str:
    """
    Sends a chunk of text to the LLM with the master prompt and returns the corrected version.
    """
    # Choose the model. 'gemini-1.5-pro-latest' is a strong choice for this task.
    model = genai.GenerativeModel('gemini-1.5-pro-latest')
    
    prompt = MASTER_PROMPT.format(text_chunk=text_chunk)
    
    try:
        response = model.generate_content(prompt)
        return response.text.strip()
    except Exception as e:
        print(f"\n[!] Error during LLM call: {e}")
        # In case of an error, return the original chunk to avoid data loss.
        return text_chunk


def main():
    """
    Main function to run the Stage 2 processing.
    """
    parser = argparse.ArgumentParser(
        description="Stage 2: Applies LLM-based formatting to a preprocessed Markdown file.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Example Usage:\n"
               "python stage2.py [input_file] [output_file]\n"
               "If no arguments provided, uses default paths:\n"
               "  Input: saved_markdowns/stage1_format.md\n"
               "  Output: saved_markdowns/stage2_format.md"
    )
    parser.add_argument("input_file", nargs='?', default="saved_markdowns/stage1_format.md", 
                       help="The path to the Stage 1 preprocessed file. (default: saved_markdowns/stage1_format.md)")
    parser.add_argument("output_file", nargs='?', default="saved_markdowns/stage2_format.md",
                       help="The path where the final, fully formatted file will be saved. (default: saved_markdowns/stage2_format.md)")
    
    args = parser.parse_args()

    # Ensure the output directory exists
    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[*] Created output directory: {output_dir}")

    print(f"[*] Reading Stage 1 file from: {args.input_file}")
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            stage1_text = f.read()
    except FileNotFoundError:
        print(f"[!] Error: Input file not found at '{args.input_file}'", file=sys.stderr)
        sys.exit(1)

    print("[*] Splitting document into logical sections...")
    sections = split_into_sections(stage1_text)
    print(f"[*] Found {len(sections)} sections to process.")
    
    corrected_sections = []
    for i, section in enumerate(sections):
        # We can add logic here to skip sections we know are fine, like the 'References'
        heading_line = section.strip().split('\n', 1)[0]
        print(f"\n[*] Processing Section {i+1}/{len(sections)}: '{heading_line[:60]}...'")
        
        corrected_chunk = call_llm_for_correction(section)
        corrected_sections.append(corrected_chunk)
        print(f"[*] Section {i+1} processed.")

    print("\n[*] Reassembling the final document...")
    final_document = '\n\n'.join(corrected_sections)

    print(f"[*] Writing final formatted output to: {args.output_file}")
    with open(args.output_file, 'w', encoding='utf-8') as f:
        f.write(final_document)
        
    print("\n[+] Stage 2 processing complete! Your document is fully formatted.")


if __name__ == "__main__":
    main()