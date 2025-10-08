#!/usr/bin/env python3
"""
Document Structure Parser v3 - High-Accuracy Classification Engine

A robust, deterministic parser that converts unstructured markdown text into
structured JSON document model according to TEMP_SYNTAX.MD specifications.

Architecture: Hybrid Rule-Based + Feature-Aware Pipeline
- Stage 0: Preprocessing & Normalization
- Stage 1: Intelligent Block Segmentation  
- Stage 2: Deterministic Hierarchical Classification
- Stage 3: Fine-Grained Detection Logic
- Stage 4: Sub-Element Extraction
- Stage 5: Structural Context Modeling
- Stage 6: Validation & Post-Processing
"""

import json
import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass


@dataclass
class ParseConfig:
    """Configuration for parser behavior and thresholds."""
    latex_math_ratio_threshold: float = 0.3
    author_name_pattern: str = r'[A-Z][a-z]+\s[A-Z][a-z]+'
    author_semicolon_min: int = 2
    author_early_blocks_max: int = 5
    references_late_threshold: float = 0.8
    paragraph_merge_threshold: int = 100
    math_symbols_pattern: str = r'[=^_{}\\]'
    min_math_symbols: int = 3


class DocumentStructureParser:
    """
    High-accuracy document structure parser with multi-stage architecture.
    """
    
    def __init__(self, config_path: Optional[str] = None):
        """Initialize parser with configuration."""
        self.config = self._load_config(config_path)
        self.regex_patterns = self._load_regex_patterns()
        
    def _load_config(self, config_path: Optional[str]) -> ParseConfig:
        """Load configuration from YAML file or use defaults."""
        if config_path and Path(config_path).exists():
            with open(config_path, 'r') as f:
                config_data = yaml.safe_load(f)
                return ParseConfig(**config_data.get('parser', {}))
        return ParseConfig()
    
    def _load_regex_patterns(self) -> Dict[str, str]:
        """Load centralized regex patterns."""
        return {
            'heading': r'^(#{1,6})\s+(.+)$',
            'code_block': r'^```(\w*)\n(.*?)\n```$',
            'overlay_block': r'^\(>>\)(.+)$',
            'table_row': r'^\|.*\|$',
            'list_item': r'^(\s*)([-*+]|\d+\.)\s+(.+)$',
            'latex_display': r'\$\$(.*?)\$\$',
            'latex_inline': r'\$([^$\n]+?)\$',
            'inline_citation': r'\[([^\]]+?)\]',
            'image_reference': r'!\[([^\]]*)\]\(([^)]+)\)',
            'email_pattern': r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b',
            'url_pattern': r'https?://[^\s<>"]{2,}',
        }
    
    def parse_document(self, text: str) -> List[Dict[str, Any]]:
        """
        Main parsing pipeline - converts markdown text to structured JSON.
        
        Args:
            text: Raw markdown text from OCR processing
            
        Returns:
            List of structured JSON elements
        """
        # Stage 0: Preprocessing
        cleaned_text = self._preprocess_text(text)
        
        # Stage 1: Intelligent Block Segmentation
        blocks = self._segment_blocks(cleaned_text)
        
        # Stage 2: Deterministic Hierarchical Classification
        classified_elements = self._classify_blocks(blocks)
        
        # Stage 4: Sub-Element Extraction
        enriched_elements = self._extract_sub_elements(classified_elements)
        
        # Stage 5: Structural Context Modeling
        structured_elements = self._model_document_structure(enriched_elements)
        
        # Stage 6: Validation & Post-Processing
        validated_elements = self._validate_and_postprocess(structured_elements)
        
        return validated_elements
    
    def _preprocess_text(self, text: str) -> str:
        """
        Stage 0: Clean OCR output and normalize formatting.
        
        - Normalize newlines (\\r\\n → \\n)
        - Replace OCR misreads (\\$ → $)
        - Collapse single newlines within paragraphs into spaces
        - Preserve double newlines as block boundaries
        - Standardize LaTeX delimiters
        """
        # Normalize line endings
        text = re.sub(r'\r\n?', '\n', text.strip())
        
        # Replace common OCR misreads
        text = text.replace('\\$', '$')
        text = text.replace('\\[', '$$').replace('\\]', '$$')
        text = text.replace('\\(', '$').replace('\\)', '$')
        
        # Collapse single newlines within paragraphs (preserve double newlines)
        text = re.sub(r'(?<!\n)\n(?!\n)', ' ', text)
        
        return text
    
    def _segment_blocks(self, text: str) -> List[str]:
        """
        Stage 1: Split document into semantically coherent blocks.
        
        Uses double newlines as hard boundaries while preserving
        block integrity for formulas, code, and tables.
        """
        blocks = re.split(r'\n{2,}', text)
        merged_blocks = []
        buffer = ''
        
        for block in blocks:
            block = block.strip()
            if not block:
                continue
                
            # Check if this is a table continuation
            if re.match(r'^\|.*\|$', block):
                if buffer and not re.match(r'^\|.*\|$', buffer):
                    merged_blocks.append(buffer.strip())
                    buffer = ''
                buffer += '\n' + block
            else:
                if buffer:
                    merged_blocks.append(buffer.strip())
                    buffer = ''
                merged_blocks.append(block)
        
        if buffer:
            merged_blocks.append(buffer.strip())
            
        return [b for b in merged_blocks if b]
    
    def _classify_blocks(self, blocks: List[str]) -> List[Dict[str, Any]]:
        """
        Stage 2: Apply classification rules in strict priority order.
        
        Detection Priority (highest to lowest):
        1. Overlay Block
        2. Code Block  
        3. Heading
        4. Abstract
        5. Author Section
        6. Table
        7. Figure/Image
        8. LaTeX Formula
        9. List
        10. References Section
        11. Paragraph (default)
        """
        classified_elements = []
        total_blocks = len(blocks)
        
        for i, block in enumerate(blocks):
            element = self._classify_single_block(block, i, total_blocks)
            classified_elements.append(element)
            
        return classified_elements
    
    def _classify_single_block(self, block: str, index: int, total_blocks: int) -> Dict[str, Any]:
        """Classify a single block using priority-based rules."""
        
        # Priority 1: Overlay Block
        if self._is_overlay_block(block):
            return {
                "element_type": "overlay_block",
                "content": block[4:].strip(),  # Remove (>>) prefix
                "metadata": {"block_index": index}
            }
        
        # Priority 2: Code Block
        if self._is_code_block(block):
            match = re.match(self.regex_patterns['code_block'], block, re.DOTALL)
            if match:
                language = match.group(1) if match.group(1) else ""
                content = match.group(2)
                return {
                    "element_type": "code_block",
                    "content": content,
                    "language": language,
                    "metadata": {"block_index": index}
                }
        
        # Priority 3: Heading
        if self._is_heading(block):
            match = re.match(self.regex_patterns['heading'], block)
            if match:
                level = len(match.group(1))
                content = match.group(2)
                return {
                    "element_type": "heading",
                    "content": content,
                    "level": level,
                    "metadata": {"block_index": index}
                }
        
        # Priority 4: Abstract
        if self._is_abstract(block, index):
            return {
                "element_type": "abstract",
                "content": block,
                "metadata": {"block_index": index}
            }
        
        # Priority 5: Author Section
        if self._is_author_section(block, index):
            return {
                "element_type": "author_section",
                "content": block,
                "metadata": {"block_index": index}
            }
        
        # Priority 6: Table
        if self._is_table(block):
            return {
                "element_type": "table",
                "content": block,
                "metadata": {"block_index": index}
            }
        
        # Priority 7: Figure/Image
        if self._is_figure_image(block):
            return {
                "element_type": "figure_image",
                "content": block,
                "metadata": {"block_index": index}
            }
        
        # Priority 8: LaTeX Formula
        if self._is_latex_formula(block):
            return {
                "element_type": "latex_formula",
                "content": block,
                "metadata": {"block_index": index}
            }
        
        # Priority 9: List
        if self._is_list(block):
            return {
                "element_type": "list",
                "content": block,
                "metadata": {"block_index": index}
            }
        
        # Priority 10: References Section
        if self._is_references_section(block, index, total_blocks):
            return {
                "element_type": "references",
                "content": block,
                "metadata": {"block_index": index}
            }
        
        # Priority 11: Paragraph (default)
        return {
            "element_type": "paragraph",
            "content": block,
            "metadata": {"block_index": index}
        }
    
    def _is_overlay_block(self, block: str) -> bool:
        """Check if block is an overlay block starting with (>>)."""
        return block.strip().startswith('(>>)')
    
    def _is_code_block(self, block: str) -> bool:
        """Check if block is a fenced code block."""
        return block.strip().startswith('```') and block.strip().endswith('```')
    
    def _is_heading(self, block: str) -> bool:
        """Check if block is a heading (starts with 1-6 # symbols)."""
        return bool(re.match(self.regex_patterns['heading'], block.strip()))
    
    def _is_abstract(self, block: str, index: int) -> bool:
        """Check if block is an abstract section."""
        return (index < 10 and 
                block.lower().strip().startswith('abstract'))
    
    def _is_author_section(self, block: str, index: int) -> bool:
        """Check if block is an author section with enhanced heuristics."""
        if index >= self.config.author_early_blocks_max:
            return False
            
        if block.count(';') < self.config.author_semicolon_min:
            return False
            
        # Check for name pattern (First Last)
        if not re.search(self.config.author_name_pattern, block):
            return False
            
        # Check for contact hints (email or URL)
        has_contact = (re.search(self.regex_patterns['email_pattern'], block) or
                      re.search(self.regex_patterns['url_pattern'], block))
        
        return True
    
    def _is_table(self, block: str) -> bool:
        """Check if block is a table (contains | characters)."""
        lines = block.strip().split('\n')
        pipe_lines = sum(1 for line in lines if '|' in line)
        return pipe_lines >= 2 and len(lines) > 1
    
    def _is_figure_image(self, block: str) -> bool:
        """Check if block is a figure or image reference."""
        return bool(re.search(self.regex_patterns['image_reference'], block))
    
    def _is_latex_formula(self, block: str) -> bool:
        """Enhanced LaTeX detection with context awareness."""
        # Check for LaTeX delimiters
        if not re.search(r'\${1,2}.*?\${1,2}', block, re.DOTALL):
            return False
            
        # Calculate math symbol ratio
        math_symbols = len(re.findall(self.config.math_symbols_pattern, block))
        total_chars = len(block)
        
        if total_chars == 0:
            return False
            
        math_ratio = math_symbols / total_chars
        
        # Check for display math ($$) or high math content
        has_display_math = '$$' in block
        has_sufficient_math = (math_ratio > self.config.latex_math_ratio_threshold or
                             math_symbols >= self.config.min_math_symbols)
        
        return has_display_math or has_sufficient_math
    
    def _is_list(self, block: str) -> bool:
        """Check if block is a list (bullet points or numbered)."""
        lines = block.strip().split('\n')
        list_lines = sum(1 for line in lines 
                        if re.match(r'^(\s*)([-*+]|\d+\.)\s+', line.strip()))
        return list_lines >= 1 and list_lines >= len(lines) * 0.5
    
    def _is_references_section(self, block: str, index: int, total_blocks: int) -> bool:
        """Check if block is a references section."""
        return ('references' in block.lower() and 
                index > self.config.references_late_threshold * total_blocks)
    
    def _extract_sub_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 4: Extract sub-elements like citations, author fields, etc.
        """
        enriched_elements = []
        
        for element in elements:
            enriched_element = element.copy()
            
            # Extract inline citations from paragraphs
            if element["element_type"] == "paragraph":
                citations = re.findall(self.regex_patterns['inline_citation'], 
                                     element["content"])
                if citations:
                    enriched_element["inline_citations"] = [
                        {"id": citation} for citation in citations
                    ]
            
            # Parse author fields from author sections
            elif element["element_type"] == "author_section":
                parts = [p.strip() for p in element["content"].split(';') if p.strip()]
                enriched_element["author_fields"] = {
                    "name": parts[0] if len(parts) > 0 else None,
                    "institution": parts[1] if len(parts) > 1 else None,
                    "contact": parts[2] if len(parts) > 2 else None,
                    "website": parts[3] if len(parts) > 3 else None
                }
            
            # Extract LaTeX reference key if present
            elif element["element_type"] == "latex_formula":
                # Check for reference key like [Eq.1] after formula
                key_match = re.search(r'\[([^\]]+)\]$', element["content"])
                if key_match:
                    enriched_element["reference_key"] = key_match.group(1)
                    # Remove key from content
                    enriched_element["content"] = re.sub(r'\s*\[[^\]]+\]$', '', 
                                                       element["content"])
            
            enriched_elements.append(enriched_element)
            
        return enriched_elements
    
    def _model_document_structure(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 5: Organize elements hierarchically under headings.
        """
        structured_elements = []
        current_section = {"heading": None, "elements": []}
        
        for element in elements:
            if element["element_type"] == "heading":
                # Save previous section if it has elements
                if current_section["elements"]:
                    structured_elements.append(current_section)
                
                # Start new section
                current_section = {"heading": element, "elements": []}
            else:
                current_section["elements"].append(element)
        
        # Add final section
        if current_section["elements"]:
            structured_elements.append(current_section)
            
        # Flatten back to element list for now (can be enhanced later)
        flattened_elements = []
        for section in structured_elements:
            if section["heading"]:
                flattened_elements.append(section["heading"])
            flattened_elements.extend(section["elements"])
            
        return flattened_elements
    
    def _validate_and_postprocess(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 6: Final validation and post-processing.
        """
        # Merge consecutive small paragraphs
        merged_elements = []
        i = 0
        
        while i < len(elements):
            current = elements[i]
            
            # Check if we should merge with next paragraph
            if (current["element_type"] == "paragraph" and 
                i + 1 < len(elements) and 
                elements[i + 1]["element_type"] == "paragraph" and
                len(current["content"]) < self.config.paragraph_merge_threshold):
                
                # Merge paragraphs
                merged_content = current["content"] + " " + elements[i + 1]["content"]
                merged_element = {
                    "element_type": "paragraph",
                    "content": merged_content,
                    "metadata": current["metadata"]
                }
                
                # Extract citations from merged content
                citations = re.findall(self.regex_patterns['inline_citation'], 
                                     merged_content)
                if citations:
                    merged_element["inline_citations"] = [
                        {"id": citation} for citation in citations
                    ]
                
                merged_elements.append(merged_element)
                i += 2  # Skip next element as it's merged
            else:
                merged_elements.append(current)
                i += 1
        
        # Ensure reference section appears last
        references_elements = [e for e in merged_elements if e["element_type"] == "references"]
        other_elements = [e for e in merged_elements if e["element_type"] != "references"]
        
        return other_elements + references_elements


def main():
    """Main function to run the parser."""
    import argparse
    
    parser = argparse.ArgumentParser(description='Document Structure Parser v3')
    parser.add_argument('input_file', help='Input markdown file')
    parser.add_argument('-o', '--output', default='output_structure.json', 
                       help='Output JSON file')
    parser.add_argument('-c', '--config', help='Configuration YAML file')
    
    args = parser.parse_args()
    
    # Initialize parser
    doc_parser = DocumentStructureParser(args.config)
    
    # Read input file
    with open(args.input_file, 'r', encoding='utf-8') as f:
        input_text = f.read()
    
    # Parse document
    try:
        structured_elements = doc_parser.parse_document(input_text)
        
        # Write output
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(structured_elements, f, indent=4, ensure_ascii=False)
        
        print(f"Successfully parsed document!")
        print(f"Input: {args.input_file}")
        print(f"Output: {args.output}")
        print(f"Total elements: {len(structured_elements)}")
        
        # Print element type distribution
        element_types = {}
        for element in structured_elements:
            element_type = element["element_type"]
            element_types[element_type] = element_types.get(element_type, 0) + 1
        
        print("\nElement type distribution:")
        for element_type, count in sorted(element_types.items()):
            print(f"  {element_type}: {count}")
            
    except Exception as e:
        print(f"Error parsing document: {str(e)}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
