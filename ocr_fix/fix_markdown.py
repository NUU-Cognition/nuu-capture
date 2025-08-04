# fix_markdown.py
import re
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
        [f for f in output_dir.iterdir() if f.suffix in ['.jpeg', '.png', '.gif']],
        key=lambda x: (int(x.stem.split('_')[1]), int(x.stem.split('_')[3]))
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

    print(f"\n✅ Success! A new file has been saved with corrected image links:")
    print(f"   {fixed_markdown_file}")

if __name__ == "__main__":
    # The directory where your output was saved
    output_directory = "document_ocr_test"
    fix_markdown_image_links(output_directory)