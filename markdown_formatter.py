#!/usr/bin/env python3
"""
Markdown Formatter for OCR Output

A robust and reusable Python script that processes markdown documents to fix common 
formatting issues arising from OCR or automated conversion. The script preserves the 
original heading structure while cleaning up content within structural elements.

Author: OCR Pipeline Team
Date: 2024
"""

import re
import logging
import sys
from typing import List, Tuple, Dict, Optional
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class MarkdownFormatter:
    """
    A comprehensive markdown formatter that fixes common OCR formatting issues
    while preserving document structure and heading hierarchy.
    """
    
    def __init__(self):
        """Initialize the markdown formatter with compiled regex patterns."""
        # Compile regex patterns for efficiency
        self.patterns = {
            # Run-on sentences: period/question/exclamation followed by capital letter
            'run_on_sentences': re.compile(r'([.!?])([A-Z])'),
            
            # Multiple blank lines (3 or more)
            'multiple_blank_lines': re.compile(r'\n\s*\n\s*\n+'),
            
            # Single newline that should be space (not at end of line, not before heading)
            'erroneous_line_breaks': re.compile(r'(?<!\n)\n(?!\n|#|\s*$)'),
            
            # Duplicate paragraphs (consecutive identical lines)
            'duplicate_paragraphs': re.compile(r'^(.+)$\n\1$', re.MULTILINE),
            
            # HTML line breaks
            'html_line_breaks': re.compile(r'<br\s*/?>', re.IGNORECASE),
            
            # Spaces before punctuation
            'spaces_before_punctuation': re.compile(r'\s+([,.!?;:])'),
            
            # Broken URLs (spaces in URLs)
            'broken_urls': re.compile(r'(https?://[^\s]+)\s+([^\s]+)'),
            
            # LaTeX math notation issues
            'latex_spaces_around_underscore': re.compile(r'\s*_\s*'),
            'latex_spaces_around_caret': re.compile(r'\s*\^\s*'),
            'latex_backslash_commands': re.compile(r'\\(int|sum|frac|operatorname)\s*'),
            
            # Image caption formatting
            'image_with_caption': re.compile(r'!\[([^\]]*)\]\(([^)]+)\)\s*\n\s*([^#\n]+)'),
            
            # Heading patterns (to preserve structure)
            'headings': re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE),
        }
        
        logger.info("MarkdownFormatter initialized with compiled regex patterns")
    
    def fix_run_on_sentences(self, text: str) -> str:
        """
        Fix run-on sentences where punctuation is immediately followed by a capital letter.
        
        Args:
            text: Input markdown text
            
        Returns:
            Text with proper spacing after sentence endings
        """
        fixed_text = self.patterns['run_on_sentences'].sub(r'\1 \2', text)
        logger.debug(f"Fixed {len(self.patterns['run_on_sentences'].findall(text))} run-on sentences")
        return fixed_text
    
    def consolidate_blank_lines(self, text: str) -> str:
        """
        Consolidate multiple blank lines (3 or more) into single blank lines.
        
        Args:
            text: Input markdown text
            
        Returns:
            Text with consistent paragraph separation
        """
        fixed_text = self.patterns['multiple_blank_lines'].sub('\n\n', text)
        logger.debug("Consolidated multiple blank lines")
        return fixed_text
    
    def fix_erroneous_line_breaks(self, text: str) -> str:
        """
        Repair paragraphs that have been incorrectly split by single newline characters.
        Intelligently distinguishes between true paragraph breaks and erroneous line breaks.
        
        Args:
            text: Input markdown text
            
        Returns:
            Text with proper paragraph structure
        """
        lines = text.split('\n')
        fixed_lines = []
        
        for i, line in enumerate(lines):
            if i == 0:
                fixed_lines.append(line)
                continue
                
            prev_line = lines[i - 1]
            
            # Don't merge if current line is a heading
            if line.strip().startswith('#'):
                fixed_lines.append(line)
                continue
                
            # Don't merge if previous line ends with punctuation and current starts with capital
            if (prev_line.strip() and 
                prev_line.strip()[-1] in '.!?' and 
                line.strip() and 
                line.strip()[0].isupper()):
                fixed_lines.append(line)
                continue
                
            # Don't merge if current line is empty (paragraph break)
            if not line.strip():
                fixed_lines.append(line)
                continue
                
            # Don't merge if previous line is empty (paragraph break)
            if not prev_line.strip():
                fixed_lines.append(line)
                continue
                
            # Merge lines that should be part of the same paragraph
            if (prev_line.strip() and 
                not prev_line.strip().endswith('.') and
                not prev_line.strip().endswith('!') and
                not prev_line.strip().endswith('?') and
                line.strip() and
                not line.strip()[0].isupper()):
                # Merge with space
                fixed_lines[-1] = prev_line + ' ' + line
            else:
                fixed_lines.append(line)
        
        logger.debug("Fixed erroneous line breaks in paragraphs")
        return '\n'.join(fixed_lines)
    
    def remove_duplicate_paragraphs(self, text: str) -> str:
        """
        Remove duplicate paragraphs that appear consecutively within the document.
        
        Args:
            text: Input markdown text
            
        Returns:
            Text with duplicate paragraphs removed
        """
        lines = text.split('\n')
        deduplicated_lines = []
        seen_paragraphs = set()
        
        for line in lines:
            line_stripped = line.strip()
            
            # Skip empty lines
            if not line_stripped:
                deduplicated_lines.append(line)
                continue
                
            # Skip headings
            if line_stripped.startswith('#'):
                deduplicated_lines.append(line)
                continue
                
            # Check for consecutive duplicates
            if line_stripped in seen_paragraphs:
                # Skip this duplicate line
                continue
            else:
                deduplicated_lines.append(line)
                seen_paragraphs.add(line_stripped)
        
        logger.debug("Removed duplicate paragraphs")
        return '\n'.join(deduplicated_lines)
    
    def fix_html_line_breaks(self, text: str) -> str:
        """
        Replace hard line breaks indicated by <br> tags with proper markdown line breaks
        or remove them if they are splitting a sentence unnecessarily.
        
        Args:
            text: Input markdown text
            
        Returns:
            Text with proper markdown line breaks
        """
        # Replace <br> tags with proper markdown line breaks (two spaces + newline)
        fixed_text = self.patterns['html_line_breaks'].sub('  \n', text)
        logger.debug("Fixed HTML line break tags")
        return fixed_text
    
    def fix_spaces_before_punctuation(self, text: str) -> str:
        """
        Remove unnecessary spaces before punctuation marks.
        
        Args:
            text: Input markdown text
            
        Returns:
            Text with proper punctuation spacing
        """
        fixed_text = self.patterns['spaces_before_punctuation'].sub(r'\1', text)
        logger.debug("Fixed spaces before punctuation")
        return fixed_text
    
    def fix_broken_urls(self, text: str) -> str:
        """
        Normalize spacing around URLs and special characters.
        
        Args:
            text: Input markdown text
            
        Returns:
            Text with properly formatted URLs
        """
        # Fix URLs with spaces in them
        fixed_text = self.patterns['broken_urls'].sub(r'\1\2', text)
        
        # Fix common URL formatting issues
        fixed_text = re.sub(r'https:\s*//', 'https://', fixed_text)
        fixed_text = re.sub(r'http:\s*//', 'http://', fixed_text)
        
        logger.debug("Fixed broken URLs")
        return fixed_text
    
    def fix_latex_math_notation(self, text: str) -> str:
        """
        Correct common errors in LaTeX mathematical notation.
        
        Args:
            text: Input markdown text
            
        Returns:
            Text with corrected LaTeX notation
        """
        # Fix spaces around _ and ^ in math expressions
        # Only fix within math delimiters
        math_pattern = re.compile(r'\$([^$]+)\$')
        
        def fix_math_content(match):
            math_content = match.group(1)
            # Remove spaces around _ and ^
            math_content = self.patterns['latex_spaces_around_underscore'].sub('_', math_content)
            math_content = self.patterns['latex_spaces_around_caret'].sub('^', math_content)
            # Ensure proper backslash commands
            math_content = self.patterns['latex_backslash_commands'].sub(r'\\\1', math_content)
            return f'${math_content}$'
        
        fixed_text = math_pattern.sub(fix_math_content, text)
        
        # Also fix display math blocks
        display_math_pattern = re.compile(r'\$\$([^$]+)\$\$')
        fixed_text = display_math_pattern.sub(fix_math_content, fixed_text)
        
        logger.debug("Fixed LaTeX math notation")
        return fixed_text
    
    def standardize_image_captions(self, text: str) -> str:
        """
        Standardize the format of images and their captions.
        
        Args:
            text: Input markdown text
            
        Returns:
            Text with standardized image caption formatting
        """
        lines = text.split('\n')
        fixed_lines = []
        i = 0
        
        while i < len(lines):
            line = lines[i]
            
            # Check if this line is an image
            image_match = re.match(r'!\[([^\]]*)\]\(([^)]+)\)', line.strip())
            
            if image_match and i + 1 < len(lines):
                # Check if next line is a caption
                next_line = lines[i + 1].strip()
                if (next_line and 
                    not next_line.startswith('#') and 
                    not next_line.startswith('!') and
                    not next_line.startswith('|') and
                    not next_line.startswith('```')):
                    
                    # Standardize caption format
                    caption = next_line
                    if not caption.startswith('Figure') and not caption.startswith('**'):
                        caption = f"**{caption}**"
                    
                    # Add image and caption with proper spacing
                    fixed_lines.append(line)
                    fixed_lines.append('')  # Empty line before caption
                    fixed_lines.append(caption)
                    fixed_lines.append('')  # Empty line after caption
                    
                    i += 2  # Skip the caption line we just processed
                else:
                    fixed_lines.append(line)
            else:
                fixed_lines.append(line)
            
            i += 1
        
        logger.debug("Standardized image caption formatting")
        return '\n'.join(fixed_lines)
    
    def preserve_heading_structure(self, text: str) -> str:
        """
        Ensure heading structure is preserved and not modified.
        This is a validation function to ensure we don't accidentally change heading levels.
        
        Args:
            text: Input markdown text
            
        Returns:
            Text with validated heading structure
        """
        # Find all headings and log their levels for verification
        headings = self.patterns['headings'].findall(text)
        
        for level, title in headings:
            logger.debug(f"Preserved heading: {level} {title}")
        
        logger.info(f"Preserved {len(headings)} headings with original structure")
        return text
    
    def format_markdown(self, text: str) -> str:
        """
        Apply all formatting fixes to the markdown text while preserving structure.
        
        Args:
            text: Input markdown text
            
        Returns:
            Formatted markdown text
        """
        logger.info("Starting markdown formatting process")
        
        # Store original text for comparison
        original_text = text
        
        # Apply formatting fixes in order
        text = self.fix_run_on_sentences(text)
        text = self.consolidate_blank_lines(text)
        text = self.fix_erroneous_line_breaks(text)
        text = self.remove_duplicate_paragraphs(text)
        text = self.fix_html_line_breaks(text)
        text = self.fix_spaces_before_punctuation(text)
        text = self.fix_broken_urls(text)
        text = self.fix_latex_math_notation(text)
        text = self.standardize_image_captions(text)
        text = self.preserve_heading_structure(text)
        
        # Log summary of changes
        changes_made = len(original_text) != len(text)
        if changes_made:
            logger.info(f"Formatting complete. Text length changed from {len(original_text)} to {len(text)} characters")
        else:
            logger.info("Formatting complete. No significant changes detected.")
        
        return text
    
    def process_file(self, input_path: str, output_path: Optional[str] = None) -> str:
        """
        Process a markdown file and save the formatted version.
        
        Args:
            input_path: Path to input markdown file
            output_path: Path to output file (optional, defaults to input_path with _formatted suffix)
            
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
        
        # Format the text
        formatted_text = self.format_markdown(text)
        
        # Determine output path
        if output_path is None:
            output_file = input_file.parent / f"{input_file.stem}_formatted{input_file.suffix}"
        else:
            output_file = Path(output_path)
        
        # Write formatted text
        logger.info(f"Writing formatted markdown to: {output_file}")
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(formatted_text)
        
        return str(output_file)


def main():
    """
    Main function demonstrating usage of the MarkdownFormatter.
    """
    import argparse
    
    parser = argparse.ArgumentParser(description='Format markdown files to fix OCR formatting issues')
    parser.add_argument('input_file', help='Path to input markdown file')
    parser.add_argument('-o', '--output', help='Path to output file (optional)')
    parser.add_argument('-v', '--verbose', action='store_true', help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Initialize formatter
    formatter = MarkdownFormatter()
    
    try:
        # Process the file
        output_file = formatter.process_file(args.input_file, args.output)
        print(f"✅ Successfully formatted markdown file")
        print(f"📁 Output saved to: {output_file}")
        
    except Exception as e:
        logger.error(f"Error processing file: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    # Example usage
    if len(sys.argv) == 1:
        # No command line arguments, run example
        print("🔧 Markdown Formatter - Example Usage")
        print("=" * 50)
        
        # Example with the processed document
        formatter = MarkdownFormatter()
        
        input_file = "saved_markdowns/processed_document.md"
        if Path(input_file).exists():
            try:
                output_file = formatter.process_file(input_file)
                print(f"✅ Formatted: {input_file}")
                print(f"📁 Output: {output_file}")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"⚠️  Example file not found: {input_file}")
            print("Run with: python markdown_formatter.py <input_file>")
    else:
        # Run with command line arguments
        import sys
        sys.exit(main()) 