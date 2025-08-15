# fix_markdown.py
import re
import sys
import os
import argparse
from pathlib import Path

def fix_markdown_image_links(output_dir_path):
    """
    Finds all images in the generated markdown and replaces their
    placeholder tags with tags using the correctly saved image filenames.
    """
    output_dir = Path(output_dir_path)
    markdown_file = output_dir / "document_content.md"
    fixed_markdown_file = output_dir / "pre_stage_1.md"

    if not markdown_file.exists():
        print(f"Error: Markdown file not found at {markdown_file}")
        return

    print(f"Reading original markdown file: {markdown_file}")

    # 1. Get a list of all saved image files in the correct order
    image_files = sorted(
        [f for f in output_dir.iterdir() if f.suffix in ['.jpeg', '.png', '.gif'] and f.stem.startswith('img-')],
        key=lambda x: int(x.stem.split('-')[1])  # Sort by the number after 'img-'
    )
    image_filenames = [f.name for f in image_files]
    print(f"Found {len(image_filenames)} saved images to link.")

    # 2. Read the markdown content and find all full image tags
    with open(markdown_file, 'r', encoding='utf-8') as f:
        content = f.read()

    # --- MODIFIED REGEX: Find the entire image tag to replace it completely ---
    markdown_image_tags = re.findall(r'(!\[.*?\]\(.*?\))', content)
    print(f"Found {len(markdown_image_tags)} image tags in the markdown.")

    # 3. Replace each old tag with a new one using the correct filename
    if len(markdown_image_tags) != len(image_filenames):
        print("\nWarning: The number of image tags found in the markdown")
        print(f"({len(markdown_image_tags)}) does not match the number of saved image")
        print(f"files ({len(image_filenames)}). Linking may be incorrect.")

    # --- MODIFIED REPLACEMENT LOGIC ---
    for i, old_tag in enumerate(markdown_image_tags):
        if i < len(image_filenames):
            correct_filename = image_filenames[i]
            
            # Create the new, correct tag with matching alt text and link
            new_tag = f"![{correct_filename}]({correct_filename})"
            
            print(f"Replacing '{old_tag}' with '{new_tag}'")
            # Replace the old tag with the new one, once.
            content = content.replace(old_tag, new_tag, 1)

    # 4. Save the corrected markdown to a new file
    with open(fixed_markdown_file, 'w', encoding='utf-8') as f:
        f.write(content)

    print(f"\n+ Success! A new file has been saved with corrected image links:")
    print(f"   {fixed_markdown_file}")

def main():
    """Main function with improved argument handling."""
    parser = argparse.ArgumentParser(
        description="Fix markdown image links by replacing placeholders with correct filenames.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Examples:\n"
               "  python fix_markdown.py                    # Auto-detect most recent folder\n"
               "  python fix_markdown.py demo_paper_2       # Use specific folder\n"
               "  python fix_markdown.py /path/to/folder    # Use absolute path"
    )
    parser.add_argument(
        "directory", 
        nargs='?', 
        default=None,
        help="Directory containing document_content.md and images (default: auto-detect most recent folder)"
    )
    
    args = parser.parse_args()
    
    if args.directory:
        # Use provided directory - resolve to absolute path
        output_directory = str(Path(args.directory).resolve())
        print(f"[*] Using specified directory: {output_directory}")
    else:
        # Auto-detect most recent output directory
        print("[*] Auto-detecting most recent output directory...")
        possible_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and d not in ['ocr_get', 'ocr_fix', 'txtfiles', '.git', 'venv', '__pycache__']]
        
        if possible_dirs:
            # Sort by modification time, most recent first
            possible_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            output_directory = str(Path(possible_dirs[0]).resolve())
            print(f"[*] Detected directory: {output_directory}")
        else:
            # Fallback for backward compatibility
            output_directory = str(Path("document_ocr_test").resolve())
            print(f"[*] No directories found, using fallback: {output_directory}")
    
    # Check if directory exists
    if not os.path.exists(output_directory):
        print(f"[!] Error: Directory '{output_directory}' does not exist.")
        print("[!] Available directories:")
        dirs = [d for d in os.listdir('.') if os.path.isdir(d) and d not in ['ocr_get', 'ocr_fix', 'txtfiles', '.git', 'venv', '__pycache__']]
        for d in sorted(dirs):
            print(f"    - {d}")
        sys.exit(1)
    
    # Check if document_content.md exists in the directory
    markdown_path = os.path.join(output_directory, "document_content.md")
    if not os.path.exists(markdown_path):
        print(f"[!] Error: 'document_content.md' not found in '{output_directory}'")
        print(f"[!] Make sure you've run 'python ocr_get/process_pdf.py' first.")
        sys.exit(1)
    
    fix_markdown_image_links(output_directory)

if __name__ == "__main__":
    main()