# MinerU API Integration

This module provides integration with the MinerU API for parsing PDF documents into structured Markdown and JSON formats.

## Features

- **PDF Upload**: Upload PDF documents to MinerU cloud storage
- **Document Parsing**: Parse PDFs with OCR and formula recognition
- **Result Download**: Automatically download and extract Markdown and JSON results
- **Progress Tracking**: Real-time progress updates during parsing
- **Error Handling**: Comprehensive error handling with retries

## Setup

### 1. API Key

Get your MinerU API key from [mineru.net](https://mineru.net) and add it to your `.env` file:

```bash
MINER_U_API_KEY=your_api_key_here
```

### 2. Dependencies

The required dependencies are already in `txtfiles/requirements.md`:

```
fastapi==0.104.1
uvicorn==0.24.0
python-dotenv==1.0.0
httpx==0.25.2
requests==2.31.0
```

## Usage

### Python Client

```python
from minerU.api.client import MinerUClient

# Initialize client (reads API key from environment)
client = MinerUClient()

# Parse a PDF document
markdown_path, json_path = client.parse_document(
    file_path="path/to/document.pdf",
    output_dir="output/directory",
    is_ocr=True,           # Enable OCR for scanned documents
    enable_formula=True    # Enable formula recognition
)

print(f"Markdown saved to: {markdown_path}")
print(f"JSON saved to: {json_path}")
```

### FastAPI Server

Start the API server:

```bash
cd nuu-capture
python minerU/api/server.py
```

The server will start on `http://localhost:8001` by default.

#### API Endpoints

**POST /parse**

Parse a PDF document.

```bash
curl -X POST "http://localhost:8001/parse" \
  -F "file=@document.pdf" \
  -F "enable_ocr=true" \
  -F "enable_formula=true"
```

Response:

```json
{
  "success": true,
  "message": "Document parsed successfully",
  "markdown_path": "minerU/outputs/document/document.md",
  "json_path": "minerU/outputs/document/document.json",
  "output_dir": "minerU/outputs/document"
}
```

**GET /health**

Health check endpoint.

```bash
curl http://localhost:8001/health
```

### Testing

Run the test script with the example PDF:

```bash
cd nuu-capture
python minerU/api/test_client.py
```

This will:
1. Upload `minerU/example/doc.pdf`
2. Submit a parsing task
3. Poll for completion
4. Download and extract results to `minerU/outputs/example_doc/`

## Output Files

After parsing, the following files are created in the output directory:

- `document.md` - Markdown version of the document
- `document.json` - JSON structure with detailed content information
- Images and other assets (if present in the original PDF)

## Architecture

### Client (`client.py`)

The `MinerUClient` class handles:

1. **File Upload**: Uploads PDFs to MinerU's OSS storage using signed URLs
2. **Task Submission**: Creates parsing tasks with specified options
3. **Status Polling**: Monitors task progress until completion
4. **Result Download**: Downloads and extracts the ZIP file containing results

### Server (`server.py`)

FastAPI server that provides:

- REST API endpoints for document parsing
- File upload handling
- Automatic result extraction
- Error handling and validation

### Workflow

```
1. Request upload URL from MinerU
2. Upload PDF to signed OSS URL
3. Submit parsing task with document URL
4. Poll task status (with progress updates)
5. Download results ZIP when complete
6. Extract Markdown and JSON files
```

## API Limits

- Maximum file size: 200MB
- Maximum pages: 600
- Daily quota: 2000 pages at highest priority

## Error Handling

The client includes comprehensive error handling for:

- File not found errors
- Upload failures (403 Forbidden, etc.)
- API errors (invalid responses, timeouts)
- Task failures (parsing errors)
- Download/extraction errors

Timeouts:
- Task completion: 10 minutes (120 attempts × 5 seconds)
- Can be adjusted in `parse_document()` method

## Development

### Debug Mode

Enable debug output in `debug_api.py` to test API responses:

```bash
python minerU/api/debug_api.py
```

### Custom Configuration

The client can be initialized with a custom API key:

```python
client = MinerUClient(api_key="your_custom_key")
```

Server host and port can be configured via environment variables:

```bash
HOST=0.0.0.0
PORT=8001
```

## Integration with nuu-surf-editor

The nuu-surf-editor can query this API to parse PDF documents:

```typescript
// Example usage from Next.js
const formData = new FormData()
formData.append('file', pdfFile)
formData.append('enable_ocr', 'true')
formData.append('enable_formula', 'true')

const response = await fetch('http://localhost:8001/parse', {
  method: 'POST',
  body: formData
})

const result = await response.json()
// result.markdown_path and result.json_path contain the parsed document
```

## Troubleshooting

### 403 Forbidden during upload

- Ensure you're not adding extra headers to signed OSS URLs
- The client automatically handles this by not adding Content-Type headers

### Task not found or 404 errors

- Tasks may take a few seconds to appear after upload
- The client includes a 10-second wait after upload before checking status

### API key errors

- Verify your API key is correctly set in `.env`
- Check that the key is valid at [mineru.net](https://mineru.net)

### Timeout errors

- Large documents may take longer than 10 minutes
- Increase `max_retries` in `parse_document()` if needed

## References

- [MinerU Official Documentation](https://mineru.net/doc/docs/index_en/)
- [MinerU API Documentation](https://mineru.net/apiManage/docs)
- [MinerU GitHub Repository](https://github.com/opendatalab/MinerU)
