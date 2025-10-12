"""FastAPI server for MinerU document parsing."""

import os
import tempfile
from pathlib import Path
from typing import Dict, Any
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from dotenv import load_dotenv

from .client import MinerUClient

load_dotenv()

app = FastAPI(
    title="MinerU Document Parsing API",
    description="API for parsing PDF documents using MinerU",
    version="1.0.0"
)


class ParseResponse(BaseModel):
    """Response model for document parsing."""

    success: bool
    message: str
    markdown_path: str | None = None
    json_path: str | None = None
    output_dir: str | None = None


@app.get("/")
async def root() -> Dict[str, str]:
    """Root endpoint."""
    return {
        "message": "MinerU Document Parsing API",
        "version": "1.0.0",
        "endpoints": {
            "/parse": "POST - Parse a PDF document",
            "/health": "GET - Health check"
        }
    }


@app.get("/health")
async def health_check() -> Dict[str, str]:
    """Health check endpoint."""
    return {"status": "healthy"}


@app.post("/parse", response_model=ParseResponse)
async def parse_document(
    file: UploadFile = File(...),
    enable_ocr: bool = True,
    enable_formula: bool = True
) -> ParseResponse:
    """
    Parse a PDF document using MinerU API.

    Args:
        file: The PDF file to parse (multipart/form-data).
        enable_ocr: Whether to enable OCR for scanned documents.
        enable_formula: Whether to enable formula recognition.

    Returns:
        ParseResponse containing paths to the markdown and JSON outputs.

    Raises:
        HTTPException: If parsing fails.
    """
    # Validate file type
    if not file.filename or not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported"
        )

    # Create temporary file for upload
    temp_file_path: str | None = None
    output_dir: str | None = None

    try:
        # Save uploaded file temporarily
        with tempfile.NamedTemporaryFile(delete=False, suffix='.pdf') as temp_file:
            temp_file_path = temp_file.name
            content: bytes = await file.read()
            temp_file.write(content)

        # Create output directory based on filename
        filename_stem: str = Path(file.filename).stem
        output_dir = os.path.join("minerU", "outputs", filename_stem)
        os.makedirs(output_dir, exist_ok=True)

        # Initialize MinerU client
        client = MinerUClient()

        # Parse the document
        markdown_path, json_path = client.parse_document(
            file_path=temp_file_path,
            output_dir=output_dir,
            is_ocr=enable_ocr,
            enable_formula=enable_formula
        )

        return ParseResponse(
            success=True,
            message="Document parsed successfully",
            markdown_path=markdown_path,
            json_path=json_path,
            output_dir=output_dir
        )

    except ValueError as e:
        raise HTTPException(
            status_code=400,
            detail=f"Invalid input: {str(e)}"
        )
    except TimeoutError as e:
        raise HTTPException(
            status_code=504,
            detail=f"Parsing timeout: {str(e)}"
        )
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Parsing failed: {str(e)}"
        )
    finally:
        # Clean up temporary file
        if temp_file_path and os.path.exists(temp_file_path):
            try:
                os.remove(temp_file_path)
            except Exception as e:
                print(f"Warning: Failed to remove temporary file {temp_file_path}: {e}")


if __name__ == "__main__":
    import uvicorn

    # Get host and port from environment or use defaults
    host: str = os.getenv("HOST", "0.0.0.0")
    port: int = int(os.getenv("PORT", "8001"))

    print(f"Starting MinerU API server on {host}:{port}")
    uvicorn.run(app, host=host, port=port)
