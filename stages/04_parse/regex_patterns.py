#!/usr/bin/env python3
"""
Centralized Regex Pattern Definitions for Document Structure Parser

This module contains all regex patterns used throughout the parser,
ensuring consistency and maintainability.
"""

import re
from typing import Dict, Pattern


class RegexPatterns:
    """Centralized collection of regex patterns for document parsing."""
    
    # Basic element patterns
    HEADING = re.compile(r'^(#{1,6})\s+(.+)$', re.MULTILINE)
    CODE_BLOCK = re.compile(r'^```(\w*)\n(.*?)\n```$', re.DOTALL)
    OVERLAY_BLOCK = re.compile(r'^\(>>\)(.+)$', re.MULTILINE)
    LIST_ITEM = re.compile(r'^(\s*)([-*+]|\d+\.)\s+(.+)$', re.MULTILINE)
    
    # Table patterns
    TABLE_ROW = re.compile(r'^\|.*\|$', re.MULTILINE)
    TABLE_SEPARATOR = re.compile(r'^\|[\s\-\|:]+\|$', re.MULTILINE)
    
    # LaTeX and math patterns
    LATEX_DISPLAY = re.compile(r'\$\$(.*?)\$\$', re.DOTALL)
    LATEX_INLINE = re.compile(r'\$([^$\n]+?)\$')
    LATEX_ENVIRONMENT = re.compile(r'\\begin\{(\w+)\}.*?\\end\{\1\}', re.DOTALL)
    MATH_SYMBOLS = re.compile(r'[=^_{}\\\]]')
    
    # Citation and reference patterns
    INLINE_CITATION = re.compile(r'\[([^\]]+?)\]')
    REFERENCE_ENTRY = re.compile(r'^\[(\d+)\]\s+(.+)$', re.MULTILINE)
    IEEE_REFERENCE = re.compile(r'^\[(\d+)\]\s+([^,]+),\s*"([^"]+)",\s*([^,]+),\s*(\d{4})', re.MULTILINE)
    
    # Author and contact patterns
    AUTHOR_NAME = re.compile(r'[A-Z][a-z]+\s[A-Z][a-z]+')
    EMAIL_PATTERN = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
    URL_PATTERN = re.compile(r'https?://[^\s<>"]{2,}')
    ORCID_PATTERN = re.compile(r'\b\d{4}-\d{4}-\d{4}-\d{3}[\dX]\b')
    
    # Image and figure patterns
    IMAGE_REFERENCE = re.compile(r'!\[([^\]]*)\]\(([^)]+)\)')
    FIGURE_CAPTION = re.compile(r'^\s*Figure\s+\d+:', re.IGNORECASE | re.MULTILINE)
    TABLE_CAPTION = re.compile(r'^\s*Table\s+\d+:', re.IGNORECASE | re.MULTILINE)
    
    # Document structure patterns
    ABSTRACT_PATTERN = re.compile(r'^\s*abstract\s*$', re.IGNORECASE | re.MULTILINE)
    INTRODUCTION_PATTERN = re.compile(r'^\s*(1\.?\s+)?introduction\s*$', re.IGNORECASE | re.MULTILINE)
    CONCLUSION_PATTERN = re.compile(r'^\s*(conclusion|conclusions)\s*$', re.IGNORECASE | re.MULTILINE)
    REFERENCES_PATTERN = re.compile(r'^\s*references?\s*$', re.IGNORECASE | re.MULTILINE)
    
    # Section numbering patterns
    SECTION_NUMBER = re.compile(r'^\s*(\d+\.?\d*\.?\d*)\s+(.+)$', re.MULTILINE)
    SUBSECTION_NUMBER = re.compile(r'^\s*(\d+\.\d+\.?\d*)\s+(.+)$', re.MULTILINE)
    
    # Content analysis patterns
    WHITESPACE = re.compile(r'\s+')
    NEWLINE_PATTERNS = re.compile(r'\r\n?')
    PUNCTUATION = re.compile(r'[.!?;:,]')
    
    # LaTeX-specific patterns
    LATEX_COMMAND = re.compile(r'\\[a-zA-Z]+\{[^}]*\}')
    LATEX_DISPLAY_MATH = re.compile(r'\$\$.*?\$\$', re.DOTALL)
    LATEX_INLINE_MATH = re.compile(r'\$[^$\n]+?\$')
    LATEX_EQUATION_LABEL = re.compile(r'\\label\{([^}]+)\}')
    LATEX_CITE = re.compile(r'\\cite\{([^}]+)\}')
    LATEX_REF = re.compile(r'\\ref\{([^}]+)\}')
    
    # Academic paper specific patterns
    DOI_PATTERN = re.compile(r'doi:\s*([^\s]+)', re.IGNORECASE)
    ARXIV_PATTERN = re.compile(r'arxiv:\s*([^\s]+)', re.IGNORECASE)
    PUBLICATION_YEAR = re.compile(r'\b(19|20)\d{2}\b')
    
    # Formatting and cleanup patterns
    BOLD_TEXT = re.compile(r'\*\*(.*?)\*\*')
    ITALIC_TEXT = re.compile(r'\*(.*?)\*')
    CODE_INLINE = re.compile(r'`([^`]+)`')
    STRIKETHROUGH = re.compile(r'~~(.*?)~~')
    
    # Block boundary patterns
    DOUBLE_NEWLINE = re.compile(r'\n{2,}')
    SINGLE_NEWLINE = re.compile(r'(?<!\n)\n(?!\n)')
    
    @classmethod
    def get_all_patterns(cls) -> Dict[str, Pattern]:
        """Return all patterns as a dictionary."""
        patterns = {}
        for attr_name in dir(cls):
            if not attr_name.startswith('_') and isinstance(getattr(cls, attr_name), Pattern):
                patterns[attr_name.lower()] = getattr(cls, attr_name)
        return patterns
    
    @classmethod
    def get_pattern(cls, name: str) -> Pattern:
        """Get a specific pattern by name."""
        pattern_name = name.upper()
        if hasattr(cls, pattern_name):
            return getattr(cls, pattern_name)
        raise ValueError(f"Pattern '{name}' not found")
    
    @classmethod
    def compile_custom_pattern(cls, pattern: str, flags: int = 0) -> Pattern:
        """Compile a custom regex pattern."""
        return re.compile(pattern, flags)


class PatternMatchers:
    """Utility functions for pattern matching and extraction."""
    
    @staticmethod
    def extract_math_content(text: str) -> Dict[str, list]:
        """Extract all mathematical content from text."""
        display_math = RegexPatterns.LATEX_DISPLAY.findall(text)
        inline_math = RegexPatterns.LATEX_INLINE.findall(text)
        
        return {
            'display_math': display_math,
            'inline_math': inline_math,
            'total_math_symbols': len(RegexPatterns.MATH_SYMBOLS.findall(text))
        }
    
    @staticmethod
    def extract_citations(text: str) -> list:
        """Extract all inline citations from text."""
        return RegexPatterns.INLINE_CITATION.findall(text)
    
    @staticmethod
    def extract_author_info(text: str) -> Dict[str, list]:
        """Extract author-related information from text."""
        names = RegexPatterns.AUTHOR_NAME.findall(text)
        emails = RegexPatterns.EMAIL_PATTERN.findall(text)
        urls = RegexPatterns.URL_PATTERN.findall(text)
        orcids = RegexPatterns.ORCID_PATTERN.findall(text)
        
        return {
            'names': names,
            'emails': emails,
            'urls': urls,
            'orcids': orcids,
            'semicolon_count': text.count(';')
        }
    
    @staticmethod
    def extract_references(text: str) -> list:
        """Extract reference entries from text."""
        return RegexPatterns.REFERENCE_ENTRY.findall(text)
    
    @staticmethod
    def calculate_math_ratio(text: str) -> float:
        """Calculate the ratio of mathematical symbols to total characters."""
        math_symbols = len(RegexPatterns.MATH_SYMBOLS.findall(text))
        total_chars = len(text.strip())
        return math_symbols / max(total_chars, 1)
    
    @staticmethod
    def is_table_content(text: str) -> bool:
        """Check if text content appears to be a table."""
        lines = text.strip().split('\n')
        if len(lines) < 2:
            return False
            
        pipe_lines = sum(1 for line in lines if '|' in line)
        return pipe_lines >= 2 and pipe_lines >= len(lines) * 0.5
    
    @staticmethod
    def is_list_content(text: str) -> bool:
        """Check if text content appears to be a list."""
        lines = text.strip().split('\n')
        list_lines = sum(1 for line in lines 
                        if RegexPatterns.LIST_ITEM.match(line.strip()))
        return list_lines >= 1 and list_lines >= len(lines) * 0.5
    
    @staticmethod
    def clean_ocr_artifacts(text: str) -> str:
        """Clean common OCR artifacts from text."""
        # Normalize line endings
        text = RegexPatterns.NEWLINE_PATTERNS.sub('\n', text)
        
        # Fix common OCR misreads
        text = text.replace('\\$', '$')
        text = text.replace('\\[', '$$').replace('\\]', '$$')
        text = text.replace('\\(', '$').replace('\\)', '$')
        
        # Collapse multiple whitespace
        text = RegexPatterns.WHITESPACE.sub(' ', text)
        
        return text.strip()


# Convenience functions for common pattern operations
def match_heading(text: str) -> tuple:
    """Extract heading level and content."""
    match = RegexPatterns.HEADING.match(text.strip())
    return (int(match.group(1)), match.group(2)) if match else (None, None)

def extract_code_block(text: str) -> tuple:
    """Extract language and content from code block."""
    match = RegexPatterns.CODE_BLOCK.match(text.strip())
    if match:
        return (match.group(1) or "", match.group(2))
    return (None, None)

def extract_overlay_content(text: str) -> str:
    """Extract content from overlay block."""
    match = RegexPatterns.OVERLAY_BLOCK.match(text.strip())
    return match.group(1).strip() if match else None

def count_math_symbols(text: str) -> int:
    """Count mathematical symbols in text."""
    return len(RegexPatterns.MATH_SYMBOLS.findall(text))

def has_display_math(text: str) -> bool:
    """Check if text contains display math ($$...$$)."""
    return bool(RegexPatterns.LATEX_DISPLAY.search(text))

def has_inline_math(text: str) -> bool:
    """Check if text contains inline math ($...$)."""
    return bool(RegexPatterns.LATEX_INLINE.search(text))


if __name__ == "__main__":
    # Test the patterns
    test_text = """
    # Heading 1
    
    This is a paragraph with citations [1, 2, 3].
    
    $$E = mc^2$$
    
    Here's some inline math: $x = y + z$.
    
    ```python
    def hello():
        return "world"
    ```
    
    (>>) This is an overlay block.
    
    | Column 1 | Column 2 |
    |----------|----------|
    | Data 1   | Data 2   |
    """
    
    print("Testing regex patterns:")
    print(f"Headings found: {RegexPatterns.HEADING.findall(test_text)}")
    print(f"Citations found: {PatternMatchers.extract_citations(test_text)}")
    print(f"Math content: {PatternMatchers.extract_math_content(test_text)}")
    print(f"Is table: {PatternMatchers.is_table_content(test_text)}")
    print(f"Math ratio: {PatternMatchers.calculate_math_ratio(test_text):.3f}")
