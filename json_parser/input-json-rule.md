### High-Level Document Structure

The document is represented as a JSON array of "element" objects. Each object in the array represents a distinct block of content from the original document, such as a paragraph, a heading, or a table. The order of elements in the array corresponds to their order in the document.

Every element object must contain two primary keys:
*   `element_type`: A string that specifies the type of the content block.
*   `metadata`: An object containing metadata, which must include a `block_index` to preserve the original sequence of the document.

---

### Element Type Schemas

Below are the detailed schemas for each `element_type`.

#### 1. `title`
Represents the main title of the document.

*   **`element_type`**: `"title"` (String, Required)
*   **`content`**: The text of the document title. (String, Required)
*   **`metadata`**:
    *   **`block_index`**: The sequential position of this element in the document. (Integer, Required)

**Example:**
```json
{
    "element_type": "title",
    "content": "MARPLE: A Benchmark for Long-Horizon Inference",
    "metadata": {
        "block_index": 0
    }
}
```

#### 2. `authors`
Represents the list of authors of the document.

*   **`element_type`**: `"authors"` (String, Required)
*   **`author_fields`**: A list of objects, where each object contains details for a single author. (Array of Objects, Required)
    *   **`name`**: The full name of the author. (String, Required)
    *   **`institution`**: The author's affiliated institution or company. (String, Optional)
    *   **`contact`**: The author's contact information, such as an email address. Can be `null`. (String, Optional)
    *   **`website`**: A URL to the author's personal or professional website. Can be `null`. (String, Optional)
*   **`metadata`**:
    *   **`block_index`**: The sequential position of this element in the document. (Integer, Required)

**Example:**
```json
{
    "element_type": "authors",
    "metadata": { "block_index": 1 },
    "author_fields": [
        {
            "name": "Emily Jin",
            "institution": "Stanford University",
            "contact": null,
            "website": null
        }
    ]
}
```

#### 3. `heading`
Represents a section or subsection heading.

*   **`element_type`**: `"heading"` (String, Required)
*   **`content`**: The text of the heading. (String, Required)
*   **`level`**: The hierarchical level of the heading (e.g., 2 for `<h2>`, 3 for `<h3>`). (Integer, Required)
*   **`metadata`**:
    *   **`block_index`**: The sequential position of this element in the document. (Integer, Required)

**Example:**
```json
{
    "element_type": "heading",
    "content": "1 Introduction",
    "level": 2,
    "metadata": { "block_index": 5 }
}
```

#### 4. `paragraph`
Represents a standard block of text.

*   **`element_type`**: `"paragraph"` (String, Required)
*   **`content`**: The full text content of the paragraph. (String, Required)
*   **`inline_citations`**: A list of citation markers found within the paragraph's text. This field should only be present if citations exist. (Array of Objects, Optional)
    *   **`id`**: The identifier of the citation, which corresponds to an entry in the `references` element. (String or Integer, Required)
*   **`metadata`**:
    *   **`block_index`**: The sequential position of this element in the document. (Integer, Required)

**Example:**
```json
{
    "element_type": "paragraph",
    "content": "Long-horizon inferences are critical for solving \"whodunit\" problems in our every day lives. [14, 40].",
    "metadata": { "block_index": 6 },
    "inline_citations": [
        { "id": "14" },
        { "id": "40" }
    ]
}
```

#### 5. `list`
Represents an ordered or unordered list.

*   **`element_type`**: `"list"` (String, Required)
*   **`content`**: The full raw text of the list, with list items typically separated by newlines. (String, Required)
*   **`items`**: An array where each string is a distinct item from the list. (Array of Strings, Required)
*   **`metadata`**:
    *   **`block_index`**: The sequential position of this element in the document. (Integer, Required)

**Example:**
```json
{
    "element_type": "list",
    "content": "1. Item one.\n2. Item two.",
    "items": [
        "Item one.",
        "Item two."
    ],
    "metadata": { "block_index": 13 }
}
```

#### 6. `image`
Represents an embedded image.

*   **`element_type`**: `"image"` (String, Required)
*   **`content`**: A string containing the image source, typically in Markdown format `![alt text](path/to/image.ext)`. (String, Required)
*   **`caption`**: The descriptive text accompanying the image. Can be `null`. (String, Optional)
*   **`metadata`**:
    *   **`block_index`**: The sequential position of this element in the document. (Integer, Required)

**Example:**
```json
{
    "element_type": "image",
    "content": "![An illustrative example](img-0.jpeg)",
    "metadata": { "block_index": 8 },
    "caption": "**Figure 1:** This is a caption for the image."
}
```

#### 7. `table`
Represents a table of data.

*   **`element_type`**: `"table"` (String, Required)
*   **`content`**: The full raw text of the table, typically in a format like Markdown. (String, Required)
*   **`caption`**: The descriptive text accompanying the table. Can be `null`. (String, Optional)
*   **`metadata`**:
    *   **`block_index`**: The sequential position of this element in the document. (Integer, Required)

**Example:**
```json
{
    "element_type": "table",
    "content": "| Header 1 | Header 2 |\n|----------|----------|\n| Cell 1   | Cell 2   |",
    "metadata": { "block_index": 19 },
    "caption": "**Table 1:** This is a caption for the table."
}
```

#### 8. `latex`
Represents a mathematical formula or equation in LaTeX format.

*   **`element_type`**: `"latex"` (String, Required)
*   **`content`**: The LaTeX code for the formula. Block-level formulas are enclosed in `$$...$$`. (String, Required)
*   **`metadata`**:
    *   **`block_index`**: The sequential position of this element in the document. (Integer, Required)

**Example:**
```json
{
    "element_type": "latex",
    "content": "$$E = mc^2$$",
    "metadata": { "block_index": 52 }
}
```

#### 9. `references`
Represents the bibliography or list of references at the end of the document.

*   **`element_type`**: `"references"` (String, Required)
*   **`references`**: A list of objects, where each object is a single bibliographic entry. (Array of Objects, Required)
    *   **`id`**: The unique identifier for the reference (e.g., 1, "1", "14"), used for linking from `inline_citations`. (String or Integer, Required)
    *   **`content`**: The full formatted text of the reference. (String, Required)
*   **`metadata`**:
    *   **`block_index`**: The sequential position of this element in the document. (Integer, Required)

**Example:**
```json
{
    "element_type": "references",
    "metadata": { "block_index": 110 },
    "references": [
        {
            "id": 1,
            "content": "[1] Author, A. (Year). Title of work. Publisher."
        }
    ]
}
```