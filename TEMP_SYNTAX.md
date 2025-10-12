# Markdown Syntax Rules for JSON Converter

This document outlines the syntax rules and parsing heuristics used by the markdown to JSON converter.

## Element Types and Detection Rules

### 1. Headings
- **Syntax**: Standard markdown headings (`#`, `##`, `###`, etc.)
- **Detection**: `heading_open` tokens
- **JSON Fields**: `element_type`, `content`, `level` (1-6)

### 2. Code Blocks
- **Syntax**: Fenced code blocks with ```language
- **Detection**: `fence` tokens
- **JSON Fields**: `element_type`, `content`, `language`

### 3. List Items
- **Syntax**: Standard markdown lists (`-`, `*`, `+`)
- **Detection**: `list_item_open` tokens
- **JSON Fields**: `element_type`, `content`

### 4. Overlay Blocks
- **Syntax**: Paragraph content starting with `(>>)`
- **Detection**: `paragraph_open` token with content starting with `(>>)`
- **JSON Fields**: `element_type: "overlay_block"`, `content` (with `(>>)` prefix removed)

### 5. Author Blocks
- **Syntax**: Paragraph with multiple semicolons (`;`) appearing early in document
- **Detection**: Heuristic based on token position (< 10) and semicolon count (>= 2)
- **JSON Fields**: `element_type: "author_block"`, `content`

### 6. Paragraphs
- **Syntax**: Regular paragraph text
- **Detection**: `paragraph_open` tokens that don't match overlay or author patterns
- **JSON Fields**: `element_type: "paragraph"`, `content`, `inline_citations` (if present)

### 7. Inline Citations
- **Syntax**: Text within square brackets `[citation content]`
- **Detection**: Regex pattern `r"\[(.*?)\]"` applied to paragraph content
- **JSON Fields**: Array of objects with `id` field containing citation content

## Output Format

All elements are converted to JSON objects in a single list with the following structure:

```json
[
    {
        "element_type": "string",
        "content": "string",
        "level": 2,               // Only for headings
        "language": "python",     // Only for code blocks
        "inline_citations": [     // Only for paragraphs with citations
            {"id": "1, 2"}
        ]
    }
]
```

## Processing Order

1. Parse markdown using MarkdownIt tokenizer
2. Iterate through tokens sequentially
3. Skip `_close` and redundant `inline` tokens
4. Apply custom logic for paragraph analysis
5. Extract inline citations from paragraph content
6. Build JSON structure with appropriate fields
7. Write to `output_structure.json` with pretty formatting