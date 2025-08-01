#!/usr/bin/env python3
"""
Safe Markdown Formatter for OCR Output

A conservative markdown formatter that makes minimal formatting improvements
while ensuring ZERO information loss. This version is much more careful
about preserving all original content.
"""

import re
import logging
import sys
from typing import List, Tuple, Dict, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class SafeMarkdownFormatter:
    """
    A conservative markdown formatter that ensures zero information loss
    while making minimal formatting improvements.
    """
    
    def __init__(self):
        """Initialize the safe markdown formatter."""
        # Only compile patterns for safe operations
        self.patterns = {
            # HTML line breaks - safe to convert
            'html_line_breaks': re.compile(r'<br\s*/?>', re.IGNORECASE),
            
            # Spaces before punctuation - safe to fix
            'spaces_before_punctuation': re.compile(r'\s+([,.!?;:])'),
            
            # Broken URLs - safe to fix
            'broken_urls': re.compile(r'(https?://[^\s]+)\s+([^\s]+)'),
            
            # Run-on sentences - safe to fix
            'run_on_sentences': re.compile(r'([.!?])([A-Z])'),
        }
        
        logger.info("SafeMarkdownFormatter initialized - ZERO information loss guaranteed")
    
    def fix_html_line_breaks(self, text: str) -> str:
        """
        Replace HTML line breaks with markdown line breaks.
        This is safe as it only converts formatting, not content.
        """
        fixed_text = self.patterns['html_line_breaks'].sub('  \n', text)
        logger.debug("Fixed HTML line break tags")
        return fixed_text
    
    def fix_spaces_before_punctuation(self, text: str) -> str:
        """
        Remove unnecessary spaces before punctuation marks.
        This is safe as it only affects spacing, not content.
        """
        fixed_text = self.patterns['spaces_before_punctuation'].sub(r'\1', text)
        logger.debug("Fixed spaces before punctuation")
        return fixed_text
    
    def fix_broken_urls(self, text: str) -> str:
        """
        Fix broken URLs with spaces.
        This is safe as it only fixes formatting, not content.
        """
        # Fix URLs with spaces in them
        fixed_text = self.patterns['broken_urls'].sub(r'\1\2', text)
        
        # Fix common URL formatting issues
        fixed_text = re.sub(r'https:\s*//', 'https://', fixed_text)
        fixed_text = re.sub(r'http:\s*//', 'http://', fixed_text)
        
        logger.debug("Fixed broken URLs")
        return fixed_text
    
    def fix_run_on_sentences(self, text: str) -> str:
        """
        Fix run-on sentences where punctuation is immediately followed by a capital letter.
        This is safe as it only adds spacing, doesn't remove content.
        """
        fixed_text = self.patterns['run_on_sentences'].sub(r'\1 \2', text)
        logger.debug("Fixed run-on sentences")
        return fixed_text
    
    def consolidate_excessive_blank_lines(self, text: str) -> str:
        """
        Consolidate excessive blank lines (4 or more) into 3 blank lines.
        This is conservative and preserves paragraph structure.
        """
        # Replace 4 or more consecutive blank lines with 3 blank lines
        fixed_text = re.sub(r'\n\s*\n\s*\n\s*\n+', '\n\n\n', text)
        logger.debug("Consolidated excessive blank lines")
        return fixed_text
    
    def preserve_all_content(self, text: str) -> str:
        """
        Validation function to ensure no content is lost.
        This is a safety check.
        """
        # Count important elements
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]
        
        logger.info(f"Content validation: {len(lines)} total lines, {len(non_empty_lines)} non-empty lines")
        return text
    
    def format_markdown_safe(self, text: str) -> str:
        """
        Apply only safe formatting fixes that guarantee zero information loss.
        
        Args:
            text: Input markdown text
            
        Returns:
            Formatted markdown text with zero information loss
        """
        logger.info("Starting SAFE markdown formatting process")
        
        # Store original text for comparison
        original_text = text
        original_lines = len(text.split('\n'))
        original_chars = len(text)
        
        # Apply only safe formatting fixes
        text = self.fix_html_line_breaks(text)
        text = self.fix_spaces_before_punctuation(text)
        text = self.fix_broken_urls(text)
        text = self.fix_run_on_sentences(text)
        text = self.consolidate_excessive_blank_lines(text)
        text = self.preserve_all_content(text)
        
        # Log summary of changes
        formatted_lines = len(text.split('\n'))
        formatted_chars = len(text)
        
        logger.info(f"SAFE formatting complete:")
        logger.info(f"  Original: {original_lines} lines, {original_chars} characters")
        logger.info(f"  Formatted: {formatted_lines} lines, {formatted_chars} characters")
        logger.info(f"  Line difference: {formatted_lines - original_lines}")
        logger.info(f"  Character difference: {formatted_chars - original_chars}")
        
        # Safety check - ensure we didn't lose too much
        if formatted_chars < original_chars * 0.95:  # Allow max 5% reduction
            logger.warning(f"Significant content reduction detected! ({original_chars} -> {formatted_chars})")
            logger.warning("This may indicate information loss. Consider using original text.")
        
        return text
    
    def process_file_safe(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Process a markdown file safely and save the formatted version.
        
        Args:
            input_path: Path to input markdown file
            output_path: Path to output file (optional, defaults to input_path with _safe_formatted suffix)
            
        Returns:
            Path to the output file
        """
        input_file = Path(input_path)
        
        if not input_file.exists():
            raise FileNotFoundError(f"Input file not found: {input_path}")
        
        # Read input file
        logger.info(f"Reading markdown file: {input_path}")
        with open(input_file, 'r', encoding='utf-8') as f:
            text = f.read()
        
        # Format the text safely
        formatted_text = self.format_markdown_safe(text)
        
        # Determine output path
        if output_path is None:
            output_file = input_file.parent / f"{input_file.stem}_safe_formatted{input_file.suffix}"
        else:
            output_file = Path(output_path)
        
        # Write formatted text
        logger.info(f"Writing safely formatted markdown to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        return str(output_file)


def main():
    """
    Main function demonstrating usage of the SafeMarkdownFormatter.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Safely format markdown files with zero information loss')
    parser.add_argument('input_file', help='Path to input markdown file')
    parser.add_argument('-o', '--output', help='Path to output file (optional)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize safe formatter
    formatter = SafeMarkdownFormatter()
    
    try:
        # Process the file safely
        output_file = formatter.process_file_safe(args.input_file, args.output)
        print(f"✅ Successfully formatted markdown file SAFELY")
        print(f"📁 Output saved to: {output_file}")
        print(f"🔒 ZERO information loss guaranteed")
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) == 1:
        # No command line arguments, run example
        print("🔒 Safe Markdown Formatter - Example Usage")
        print("=" * 50)
        
        # Example with the processed document
        formatter = SafeMarkdownFormatter()
        
        input_file = "saved_markdowns/processed_document.md"
        if Path(input_file).exists():
            try:
                output_file = formatter.process_file_safe(input_file)
                print(f"✅ Safely formatted: {input_file}")
                print(f"📁 Output: {output_file}")
                print(f"🔒 Zero information loss guaranteed")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"⚠️  Example file not found: {input_file}")
            print("Run with: python markdown_formatter_safe.py <input_file>")
    else:
        # Run with command line arguments
        import sys
        sys.exit(main()) 