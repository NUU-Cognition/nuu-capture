"""Test script for MinerU API client."""

import os
import sys
from pathlib import Path

# Add parent directory to path to import client
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from minerU.api.client import MinerUClient


def test_parse_example_document() -> None:
    """Test parsing the example PDF document."""
    # Path to example document
    example_pdf: str = os.path.join("minerU", "example", "doc1.pdf")

    if not os.path.exists(example_pdf):
        print(f"Error: Example PDF not found at {example_pdf}")
        return

    # Create output directory
    output_dir: str = os.path.join("minerU", "outputs", "example_doc1")

    print("=" * 60)
    print("MinerU API Client Test")
    print("=" * 60)
    print(f"Input: {example_pdf}")
    print(f"Output: {output_dir}")
    print("=" * 60)
    print()

    try:
        # Initialize client
        client = MinerUClient()

        # Parse document
        markdown_path, json_path = client.parse_document(
            file_path=example_pdf,
            output_dir=output_dir,
            is_ocr=True,
            enable_formula=True
        )

        print()
        print("=" * 60)
        print("SUCCESS!")
        print("=" * 60)
        print(f"Markdown: {markdown_path}")
        print(f"JSON: {json_path}")
        print()

        # Show file sizes
        md_size: int = os.path.getsize(markdown_path)
        json_size: int = os.path.getsize(json_path)
        print(f"Markdown size: {md_size:,} bytes")
        print(f"JSON size: {json_size:,} bytes")

    except Exception as e:
        print()
        print("=" * 60)
        print("ERROR!")
        print("=" * 60)
        print(f"Error: {str(e)}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    test_parse_example_document()
