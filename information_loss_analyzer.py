#!/usr/bin/env python3
"""
Information Loss Analyzer for OCR Processing

This script analyzes the processed markdown documents to ensure zero information loss
between the original OCR output and the formatted version.
"""

import re
import difflib
from pathlib import Path
from collections import Counter

def load_file_content(file_path):
    """Load file content and return as string."""
    with open(file_path, 'r', encoding='utf-8') as f:
        return f.read()

def extract_sections(text):
    """Extract all sections and their content."""
    sections = {}
    current_section = "header"
    current_content = []
    
    lines = text.split('\n')
    
    for line in lines:
        # Check if line is a heading
        heading_match = re.match(r'^(#{1,6})\s+(.+)$', line)
        if heading_match:
            # Save previous section
            if current_content:
                sections[current_section] = '\n'.join(current_content).strip()
            
            # Start new section
            current_section = heading_match.group(2)
            current_content = []
        else:
            current_content.append(line)
    
    # Save last section
    if current_content:
        sections[current_section] = '\n'.join(current_content).strip()
    
    return sections

def extract_references(text):
    """Extract all references from the text."""
    # Find reference patterns like [1], [2], etc.
    references = re.findall(r'\[(\d+)\]', text)
    return set(references)

def extract_math_expressions(text):
    """Extract all mathematical expressions."""
    # Find inline math: $...$
    inline_math = re.findall(r'\$([^$]+)\$', text)
    # Find display math: $$...$$
    display_math = re.findall(r'\$\$([^$]+)\$\$', text)
    return inline_math + display_math

def extract_images(text):
    """Extract all image references."""
    # Find markdown image syntax: ![alt](src)
    images = re.findall(r'!\[([^\]]*)\]\(([^)]+)\)', text)
    return images

def extract_tables(text):
    """Extract table content."""
    # Find table patterns
    table_pattern = r'\|.*\|'
    tables = re.findall(table_pattern, text, re.MULTILINE)
    return tables

def analyze_information_loss():
    """Comprehensive analysis of potential information loss."""
    
    print("🔍 INFORMATION LOSS ANALYSIS")
    print("=" * 50)
    
    # Load both documents
    original_path = "saved_markdowns/processed_document.md"
    formatted_path = "saved_markdowns/processed_document_safe_formatted.md"
    
    if not Path(original_path).exists():
        print(f"❌ Original file not found: {original_path}")
        return
    
    if not Path(formatted_path).exists():
        print(f"❌ Formatted file not found: {formatted_path}")
        return
    
    original_content = load_file_content(original_path)
    formatted_content = load_file_content(formatted_path)
    
    print(f"📊 File Statistics:")
    print(f"   Original: {len(original_content)} characters, {len(original_content.split())} words")
    print(f"   Formatted: {len(formatted_content)} characters, {len(formatted_content.split())} words")
    print(f"   Difference: {len(original_content) - len(formatted_content)} characters")
    print()
    
    # 1. Section Analysis
    print("📋 SECTION ANALYSIS")
    print("-" * 30)
    
    original_sections = extract_sections(original_content)
    formatted_sections = extract_sections(formatted_content)
    
    print(f"Original sections: {len(original_sections)}")
    print(f"Formatted sections: {len(formatted_sections)}")
    
    # Check for missing sections
    missing_sections = set(original_sections.keys()) - set(formatted_sections.keys())
    if missing_sections:
        print(f"❌ MISSING SECTIONS: {missing_sections}")
    else:
        print("✅ All sections preserved")
    
    # Check for new sections (shouldn't happen)
    new_sections = set(formatted_sections.keys()) - set(original_sections.keys())
    if new_sections:
        print(f"⚠️  NEW SECTIONS (unexpected): {new_sections}")
    
    print()
    
    # 2. Reference Analysis
    print("📚 REFERENCE ANALYSIS")
    print("-" * 30)
    
    original_refs = extract_references(original_content)
    formatted_refs = extract_references(formatted_content)
    
    print(f"Original references: {len(original_refs)}")
    print(f"Formatted references: {len(formatted_refs)}")
    
    missing_refs = original_refs - formatted_refs
    if missing_refs:
        print(f"❌ MISSING REFERENCES: {sorted(missing_refs)}")
    else:
        print("✅ All references preserved")
    
    print()
    
    # 3. Math Expression Analysis
    print("🧮 MATH EXPRESSION ANALYSIS")
    print("-" * 30)
    
    original_math = extract_math_expressions(original_content)
    formatted_math = extract_math_expressions(formatted_content)
    
    print(f"Original math expressions: {len(original_math)}")
    print(f"Formatted math expressions: {len(formatted_math)}")
    
    missing_math = set(original_math) - set(formatted_math)
    if missing_math:
        print(f"❌ MISSING MATH EXPRESSIONS: {len(missing_math)}")
        for i, expr in enumerate(list(missing_math)[:5]):  # Show first 5
            print(f"   {i+1}. {expr[:100]}...")
    else:
        print("✅ All math expressions preserved")
    
    print()
    
    # 4. Image Analysis
    print("🖼️  IMAGE ANALYSIS")
    print("-" * 30)
    
    original_images = extract_images(original_content)
    formatted_images = extract_images(formatted_content)
    
    print(f"Original images: {len(original_images)}")
    print(f"Formatted images: {len(formatted_images)}")
    
    missing_images = set(original_images) - set(formatted_images)
    if missing_images:
        print(f"❌ MISSING IMAGES: {len(missing_images)}")
        for img in missing_images:
            print(f"   - {img}")
    else:
        print("✅ All images preserved")
    
    print()
    
    # 5. Table Analysis
    print("📊 TABLE ANALYSIS")
    print("-" * 30)
    
    original_tables = extract_tables(original_content)
    formatted_tables = extract_tables(formatted_content)
    
    print(f"Original table rows: {len(original_tables)}")
    print(f"Formatted table rows: {len(formatted_tables)}")
    
    if len(original_tables) != len(formatted_tables):
        print(f"⚠️  TABLE ROW COUNT MISMATCH: {len(original_tables)} vs {len(formatted_tables)}")
    else:
        print("✅ Table structure preserved")
    
    print()
    
    # 6. Content Comparison
    print("🔍 DETAILED CONTENT COMPARISON")
    print("-" * 30)
    
    # Split into lines for detailed comparison
    original_lines = original_content.split('\n')
    formatted_lines = formatted_content.split('\n')
    
    # Find unique lines in original that are not in formatted
    original_unique = set(original_lines) - set(formatted_lines)
    formatted_unique = set(formatted_lines) - set(original_lines)
    
    print(f"Lines unique to original: {len(original_unique)}")
    print(f"Lines unique to formatted: {len(formatted_unique)}")
    
    if original_unique:
        print("\n📝 LINES LOST FROM ORIGINAL:")
        for i, line in enumerate(list(original_unique)[:10]):  # Show first 10
            if line.strip():  # Only show non-empty lines
                print(f"   {i+1}. {line[:100]}...")
        if len(original_unique) > 10:
            print(f"   ... and {len(original_unique) - 10} more lines")
    
    if formatted_unique:
        print("\n📝 LINES ADDED TO FORMATTED:")
        for i, line in enumerate(list(formatted_unique)[:10]):  # Show first 10
            if line.strip():  # Only show non-empty lines
                print(f"   {i+1}. {line[:100]}...")
        if len(formatted_unique) > 10:
            print(f"   ... and {len(formatted_unique) - 10} more lines")
    
    print()
    
    # 7. Summary
    print("📋 SUMMARY")
    print("-" * 30)
    
    total_issues = (
        len(missing_sections) + 
        len(missing_refs) + 
        len(missing_math) + 
        len(missing_images) +
        (1 if len(original_tables) != len(formatted_tables) else 0)
    )
    
    if total_issues == 0:
        print("✅ ZERO INFORMATION LOSS DETECTED")
        print("   The formatter successfully preserved all content while improving formatting.")
    else:
        print(f"❌ {total_issues} POTENTIAL ISSUES DETECTED")
        print("   Please review the detailed analysis above.")
    
    print()
    print("=" * 50)

if __name__ == "__main__":
    analyze_information_loss() 