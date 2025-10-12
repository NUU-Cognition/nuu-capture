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
    latex_display_only: bool = True
    author_parse_individual: bool = True
    references_parse_entries: bool = True
    caption_merge_enabled: bool = True
    caption_max_distance: int = 1
    caption_patterns: list = None
    min_block_length: int = 5
    max_consecutive_merges: int = 3
    confidence_thresholds: dict = None

    def __post_init__(self):
        """Initialize default values for mutable fields."""
        if self.caption_patterns is None:
            self.caption_patterns = ['Figure\\s+\\d+:', 'Table\\s+\\d+:', 'Fig\\.\\s+\\d+:']
        if self.confidence_thresholds is None:
            self.confidence_thresholds = {}


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

        # Parse references after structure modeling (since references element is created in stage 5)
        structured_elements = self._parse_references_elements(structured_elements)

        # Stage 6: Validation & Post-Processing
        validated_elements = self._validate_and_postprocess(structured_elements)

        # Additional validation pass for author sections
        validated_elements = self._validate_author_sections(validated_elements)

        return validated_elements
    
    def _preprocess_text(self, text: str) -> str:
        """
        Stage 0: Clean OCR output and normalize formatting.

        - Normalize newlines (\\r\\n → \\n)
        - Replace OCR misreads (\\$ → $)
        - Collapse single newlines within paragraphs into spaces
        - Preserve double newlines as block boundaries
        - Preserve table structures (lines with |)
        - Standardize LaTeX delimiters
        """
        # Normalize line endings
        text = re.sub(r'\r\n?', '\n', text.strip())

        # Replace common OCR misreads
        text = text.replace('\\$', '$')
        text = text.replace('\\[', '$$').replace('\\]', '$$')
        text = text.replace('\\(', '$').replace('\\)', '$')

        # Collapse single newlines within paragraphs (preserve double newlines)
        # BUT preserve newlines in tables (lines with |), code blocks, and lists
        lines = text.split('\n')
        result_lines = []
        i = 0

        while i < len(lines):
            line = lines[i]

            # Check if this is a structural element that should preserve newlines
            is_table_line = '|' in line and line.count('|') >= 2
            is_code_fence = line.strip().startswith('```')
            is_list_item = re.match(r'^\s*([-*+]|\d+\.)\s+', line)
            is_heading = re.match(r'^\s*#{1,6}\s+', line)
            is_blank = not line.strip()

            # If structural element or blank, keep as-is
            if is_table_line or is_code_fence or is_list_item or is_heading or is_blank:
                result_lines.append(line)
                i += 1
            else:
                # Regular text line - check if we should join with next
                if i + 1 < len(lines) and lines[i + 1].strip() and not lines[i + 1].startswith((' ', '\t', '#', '-', '*', '+', '|')):
                    # Join with next line
                    line += ' ' + lines[i + 1].strip()
                    i += 2
                    while i < len(lines) and lines[i].strip() and not lines[i].startswith((' ', '\t', '#', '-', '*', '+', '|')):
                        line += ' ' + lines[i].strip()
                        i += 1
                    result_lines.append(line)
                else:
                    result_lines.append(line)
                    i += 1

        text = '\n'.join(result_lines)

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

        def is_table_block(block_text):
            """Check if a block contains table rows."""
            lines = block_text.strip().split('\n')
            pipe_lines = [l for l in lines if '|' in l and l.count('|') >= 2]
            return len(pipe_lines) >= 2

        for block in blocks:
            block = block.strip()
            if not block:
                continue

            # Check if this is a table block (multiple lines with pipes)
            if is_table_block(block):
                if buffer and not is_table_block(buffer):
                    merged_blocks.append(buffer.strip())
                    buffer = ''
                # Table blocks should not be merged with adjacent blocks
                if buffer:
                    buffer += '\n' + block
                else:
                    buffer = block
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
        if self._is_author_section(block, index, total_blocks):
            return {
                "element_type": "author",
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
                "element_type": "image",
                "content": block,
                "metadata": {"block_index": index}
            }
        
        # Priority 8: LaTeX Formula
        if self._is_latex_formula(block):
            return {
                "element_type": "latex",
                "content": block,
                "metadata": {"block_index": index}
            }
        
        # Priority 9: List
        if self._is_list(block):
            items = self._split_list_block(block)
            return {
                "element_type": "list",
                "content": block,
                "items": items,
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
    
    def _is_author_section(self, block: str, index: int, total_blocks: int) -> bool:
        """Check if block is an author section with refined heuristics and negative rules."""
        lines = [l.strip() for l in block.splitlines() if l.strip()]
        text = ' '.join(lines)

        # 🚫 Negative rules - reject if any are true
        if '|' in text:  # Likely a table
            return False
        if re.match(r'^(\d+\.)|^-|^#', text):  # Starts with list marker or heading
            return False
        if len(lines) > 5 or len(text) > 300:  # Too long for author info
            return False
        if sum(1 for l in lines if re.match(r'^\d+\.', l)) >= 2:  # Multiple numbered items
            return False

        # ✅ Positive signals - only if in early document region
        if index < 6 or index < 0.1 * total_blocks:
            # Bolded names detection
            if re.findall(r'\*\*[A-Za-z ,.\'-]+\*\*', block):
                return True
            
            # Semicolon fields with name/affiliation patterns
            if block.count(';') >= 1 and (self._has_name_pattern(block) or self._has_affiliation(block)):
                return True
            
            # Email detection
            if self._has_email(block):
                return True
            
            # Multiple lines with capitalized names
            found_names = sum(1 for l in lines if self._has_name_pattern(l))
            if found_names >= 2:
                return True
        
        return False
    
    def _has_name_pattern(self, text: str) -> bool:
        """Check for name pattern (First Last)."""
        name_pattern = re.compile(r'[A-Z][a-z]+(?:[-\']?[A-Z][a-z]+)?\s+[A-Z][a-z]+')
        return bool(name_pattern.search(text))
    
    def _has_affiliation(self, text: str) -> bool:
        """Check for affiliation keywords."""
        affiliation_pattern = re.compile(r'\b(University|Institute|Dept|College|Laboratory|Stanford|MIT|Harvard)\b', re.I)
        return bool(affiliation_pattern.search(text))
    
    def _has_email(self, text: str) -> bool:
        """Check for email pattern."""
        email_pattern = re.compile(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}')
        return bool(email_pattern.search(text))
    
    def _is_table(self, block: str) -> bool:
        """Check if block is a table with proper header separators."""
        lines = [l for l in block.splitlines() if l.strip()]
        pipe_lines = [l for l in lines if '|' in l]
        if len(pipe_lines) < 2:
            return False
        if any(re.search(r'^\s*\|?\s*:?-{2,}:?\s*(\||$)', l) for l in lines):
            return True
        counts = [l.count('|') for l in pipe_lines]
        if len(set(counts)) == 1 and counts[0] >= 2:
            return True
        return False
    
    def _is_figure_image(self, block: str) -> bool:
        """Check if block is a figure or image reference."""
        return bool(re.search(self.regex_patterns['image_reference'], block))
    
    def _is_latex_formula(self, block: str) -> bool:
        r"""
        Detect ONLY standalone display math formulas (not inline math in paragraphs).
        Only triggers for display math delimiters: $$...$$ or \[...\] or \begin{equation}
        """
        # Must have display math markers (not just inline $...$)
        has_display_math = ('$$' in block or
                           r'\[' in block or
                           r'\begin{' in block and r'\end{' in block)

        if not has_display_math:
            return False

        # Additional validation: check for math content
        # Extract display math regions only
        display_regions = re.findall(r'\$\$(.+?)\$\$', block, flags=re.S)

        if display_regions:
            # Validate that display math contains actual math content
            for region in display_regions:
                tokens = re.findall(r'\S+', region)
                if not tokens:
                    continue
                math_tokens = sum(1 for t in tokens if re.search(r'[=^_{}\\]|\\[a-zA-Z]+', t))
                if len(tokens) > 0 and math_tokens / len(tokens) > 0.15:
                    return True

        # Check for LaTeX environments (always display math)
        if r'\begin{' in block and r'\end{' in block:
            return True

        return False
    
    def _is_list(self, block: str) -> bool:
        """Check if block is a list (bullet points or numbered)."""
        lines = block.strip().split('\n')
        list_lines = sum(1 for line in lines 
                        if re.match(r'^(\s*)([-*+]|\d+\.)\s+', line.strip()))
        return list_lines >= 1 and list_lines >= len(lines) * 0.5
    
    def _split_list_block(self, block: str):
        """Split list block into individual items."""
        items = []
        list_item_re = re.compile(r'^\s*(?:[-*+]|(\d+)\.)\s+(.*)$')
        
        for line in block.splitlines():
            match = list_item_re.match(line)
            if match:
                items.append(match.group(2).strip())
            elif items and line.strip():
                items[-1] += ' ' + line.strip()
        
        return items
    
    def _extract_inline_citations(self, block: str):
        """Extract inline citations and split comma-separated ones."""
        citation_re = re.compile(r'\[([^\]]+?)\]')
        raw = citation_re.findall(block)
        out = []
        for r in raw:
            r = r.strip().rstrip('.,;:')
            for part in re.split(r'\s*,\s*', r):
                if part:
                    out.append(part)
        return out
    
    def _is_references_section(self, block: str, index: int, total_blocks: int) -> bool:
        """Check if block is a references section."""
        return ('references' in block.lower() and
                index > self.config.references_late_threshold * total_blocks)

    def _parse_individual_authors(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse author section content into individual author objects.
        Extracts bolded names (**Name**) and associated metadata.
        """
        authors = []

        # Extract bolded names (markdown format: **Name**)
        bolded_names = re.findall(r'\*\*([A-Za-z\s\.\-\']+)\*\*', content)

        # Extract affiliations (institution names)
        affiliation_patterns = [
            r'(Stanford University|MIT|Harvard|University of [A-Za-z\s]+|[A-Za-z\s]+ University)',
            r'(Institute of [A-Za-z\s]+|[A-Za-z\s]+ Institute)',
            r'([A-Za-z\s]+ Laboratory|[A-Za-z\s]+ Lab)',
            r'(Dept\.? of [A-Za-z\s]+|Department of [A-Za-z\s]+)',
            r'(College of [A-Za-z\s]+|[A-Za-z\s]+ College)'
        ]

        institutions = []
        for pattern in affiliation_patterns:
            institutions.extend(re.findall(pattern, content, re.IGNORECASE))

        # Extract emails
        emails = re.findall(r'[\w.+-]+@[\w-]+\.[a-zA-Z]{2,}', content)

        # Extract URLs
        urls = re.findall(r'https?://[^\s<>"]+', content)

        # Build author objects
        for i, name in enumerate(bolded_names):
            name = name.strip()
            # Skip if it's just asterisks or markers
            if not re.search(r'[A-Z][a-z]+', name):
                continue

            author_obj = {
                "name": name,
                "institution": institutions[0] if institutions else None,
                "contact": emails[i] if i < len(emails) else None,
                "website": urls[i] if i < len(urls) else None
            }
            authors.append(author_obj)

        # If no bolded names found, try parsing semicolon-separated format
        if not authors and ';' in content:
            parts = [p.strip() for p in content.split(';') if p.strip()]
            for part in parts:
                # Check if this part contains a name
                if re.search(r'[A-Z][a-z]+\s+[A-Z][a-z]+', part):
                    author_obj = {
                        "name": part,
                        "institution": None,
                        "contact": None,
                        "website": None
                    }
                    authors.append(author_obj)

        return authors if authors else [{"name": None, "institution": None, "contact": None, "website": None}]

    def _parse_references_list(self, content: str) -> List[Dict[str, Any]]:
        """
        Parse references section content into structured list of references.
        Extracts [id] content patterns and handles multi-line references.
        """
        references = []
        lines = content.split('\n')

        current_ref = None
        current_id = None

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Check if line starts with [number]
            match = re.match(r'^\[(\d+)\]\s*(.+)$', line)

            if match:
                # Save previous reference if exists
                if current_ref is not None and current_id is not None:
                    references.append({
                        "id": int(current_id),
                        "content": current_ref.strip()
                    })

                # Start new reference
                current_id = match.group(1)
                current_ref = f"[{current_id}] {match.group(2)}"
            else:
                # Continuation of previous reference
                if current_ref is not None:
                    current_ref += " " + line

        # Add final reference
        if current_ref is not None and current_id is not None:
            references.append({
                "id": int(current_id),
                "content": current_ref.strip()
            })

        return references

    def _extract_sub_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 4: Extract sub-elements like citations, author fields, etc.
        """
        enriched_elements = []

        for element in elements:
            enriched_element = element.copy()

            # Extract inline citations from paragraphs
            if element["element_type"] == "paragraph":
                citations = self._extract_inline_citations(element["content"])
                if citations:
                    enriched_element["inline_citations"] = [
                        {"id": citation} for citation in citations
                    ]

            # Parse author fields from author sections into individual author list
            elif element["element_type"] == "author_section":
                authors = self._parse_individual_authors(element["content"])
                enriched_element["author_fields"] = authors
                # Remove content field as per requirements
                if "content" in enriched_element:
                    del enriched_element["content"]

            # Parse references section into structured list
            elif element["element_type"] == "references":
                # Skip the heading line if it exists
                content = element["content"]
                # Remove "References" heading if present
                content = re.sub(r'^\s*#{0,6}\s*References?\s*\n', '', content, flags=re.IGNORECASE)

                references = self._parse_references_list(content)
                enriched_element["references"] = references
                # Remove content field as per requirements
                if "content" in enriched_element:
                    del enriched_element["content"]

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
    
    def _parse_references_elements(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Parse references elements that were created in structure modeling.
        Converts content field to structured references list.
        """
        parsed_elements = []

        for element in elements:
            if element["element_type"] == "references" and "content" in element:
                # Parse the references content into structured list
                content = element["content"]

                # Remove "References" heading if present
                content = re.sub(r'^\s*#{0,6}\s*References?\s*\n', '', content, flags=re.IGNORECASE)

                references = self._parse_references_list(content)
                element["references"] = references

                # Remove content field as per requirements
                del element["content"]

            parsed_elements.append(element)

        return parsed_elements

    def _model_document_structure(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 5: Organize elements hierarchically under headings.
        Also merges references section into a single element.
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

        # Flatten back to element list, but merge references section
        flattened_elements = []
        for section in structured_elements:
            if section["heading"]:
                heading = section["heading"]
                flattened_elements.append(heading)

                # Check if this is the References section
                if (heading.get("element_type") == "heading" and
                    "reference" in heading.get("content", "").lower()):

                    # Merge all reference entries into a single references element
                    reference_paragraphs = section["elements"]

                    # Check if we have reference entries (paragraphs starting with [number])
                    ref_entries = [p for p in reference_paragraphs
                                 if p.get("element_type") == "paragraph" and
                                 re.match(r'^\[\d+\]', p.get("content", ""))]

                    if ref_entries:
                        # Merge all references into single element
                        merged_content = "\n\n".join([p["content"] for p in ref_entries])
                        references_element = {
                            "element_type": "references",
                            "content": merged_content,
                            "metadata": {"block_index": heading["metadata"]["block_index"]}
                        }
                        flattened_elements.append(references_element)

                        # Add any non-reference paragraphs (e.g., after references)
                        non_ref_elements = [p for p in reference_paragraphs if p not in ref_entries]
                        flattened_elements.extend(non_ref_elements)
                    else:
                        # No references found, add elements as-is
                        flattened_elements.extend(section["elements"])
                else:
                    # Regular section, add elements as-is
                    flattened_elements.extend(section["elements"])
            else:
                # No heading for this section
                flattened_elements.extend(section["elements"])

        return flattened_elements
    
    def _validate_and_postprocess(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Stage 6: Final validation and post-processing.
        Includes caption merging for figures/tables and paragraph merging.
        """
        merged_elements = []
        i = 0

        while i < len(elements):
            current = elements[i]

            # Check if current is a figure/table and next is a caption paragraph
            if (current["element_type"] in ["figure_image", "table"] and
                i + 1 < len(elements) and
                elements[i + 1]["element_type"] == "paragraph"):

                next_elem = elements[i + 1]
                next_content = next_elem.get("content", "")

                # Check if next paragraph is a caption (starts with "Figure X:" or "Table X:")
                # Handle bold markdown formatting: **Figure 1:** or Figure 1:
                is_caption = (
                    re.match(r'^\s*\*?\*?Figure\s+\d+:\*?\*?', next_content, re.IGNORECASE) or
                    re.match(r'^\s*\*?\*?Table\s+\d+:\*?\*?', next_content, re.IGNORECASE) or
                    re.match(r'^\s*\*?\*?Fig\.?\s+\d+:\*?\*?', next_content, re.IGNORECASE)
                )

                if is_caption:
                    # Merge caption into figure/table
                    current["caption"] = next_content
                    merged_elements.append(current)
                    i += 2  # Skip the caption paragraph
                    continue

            # Check if we should merge with next paragraph (small paragraphs)
            if (current["element_type"] == "paragraph" and
                i + 1 < len(elements) and
                elements[i + 1]["element_type"] == "paragraph" and
                len(current.get("content", "")) < self.config.paragraph_merge_threshold):

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
    
    def _validate_author_sections(self, elements: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Additional validation pass to eliminate author section false positives.
        """
        validated_elements = []

        for element in elements:
            if element["element_type"] == "author_section":
                # Check if block appears too late in document
                block_index = element["metadata"].get("block_index", 0)
                if block_index > 10:
                    # Downgrade to paragraph if too late
                    element["element_type"] = "paragraph"
                    if "author_fields" in element:
                        # Convert author_fields back to content for paragraph
                        authors_str = "; ".join([a.get("name", "") for a in element["author_fields"] if a.get("name")])
                        element["content"] = authors_str
                        del element["author_fields"]

                # Check if author_fields is empty or invalid
                elif "author_fields" in element:
                    author_fields = element["author_fields"]
                    # Check if we have valid authors
                    has_valid_author = any(a.get("name") for a in author_fields if isinstance(a, dict))
                    if not has_valid_author:
                        # Downgrade to paragraph if no valid authors
                        element["element_type"] = "paragraph"
                        element["content"] = ""
                        del element["author_fields"]

            validated_elements.append(element)

        return validated_elements


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
