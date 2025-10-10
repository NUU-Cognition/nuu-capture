"""
Shared type definitions for the OCR pipeline.

This module contains type definitions used across multiple modules in the OCR pipeline
to provide better type safety and IDE support without breaking existing functionality.
"""

from typing import TypedDict, Protocol, Union, List, Dict, Any, Optional
from pathlib import Path


# Path-like types
PathLike = Union[str, Path]

# API Response Types
class MistralImageData(TypedDict):
    """Structure for image data from Mistral API."""
    image_base64: str
    type: str

class MistralPageData(TypedDict):
    """Structure for page data from Mistral API."""
    markdown: str
    images: List[MistralImageData]

class MistralOCRResponse(TypedDict):
    """Structure for complete Mistral OCR API response."""
    pages: List[MistralPageData]

# Document processing types
class DocumentPayload(TypedDict):
    """Structure for document payload sent to Mistral API."""
    type: str
    document_url: str

class ProcessingResult(TypedDict):
    """Result of a processing stage."""
    success: bool
    output_path: Optional[str]
    error_message: Optional[str]

# LLM Protocol for Stage 2
class LLMModel(Protocol):
    """Protocol for LLM models used in Stage 2 processing."""
    
    def generate_content(self, prompt: str) -> Any:
        """Generate content from a prompt."""
        ...

# Configuration types
class PipelineConfig(TypedDict, total=False):
    """Configuration for the OCR pipeline."""
    mistral_api_key: str
    gemini_api_key: str
    output_dir: Optional[str]
    skip_checks: bool
    timeout: float

# File processing types
class FileInfo(TypedDict):
    """Information about a processed file."""
    path: str
    size: int
    exists: bool
    description: str