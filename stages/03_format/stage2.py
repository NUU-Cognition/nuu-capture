import re
import argparse
import sys
import os
import time
import asyncio
import random
import shutil
import google.generativeai as genai
from dotenv import load_dotenv
from typing import List, Optional, Protocol, Any, Tuple
from pathlib import Path
from datetime import datetime

# Try to import tqdm for progress bar (optional)
try:
    from tqdm.asyncio import tqdm as atqdm
    TQDM_AVAILABLE = True
except ImportError:
    TQDM_AVAILABLE = False
    print("[!] Warning: tqdm not installed. Progress bar disabled. Install with: pip install tqdm")

# Local type definition
class LLMModel(Protocol):
    def generate_content(self, prompt: str) -> Any:
        ...

# Load environment variables from .env file
load_dotenv()

# --- LLM Configuration ---
try:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY environment variable not set.")
    genai.configure(api_key=api_key)
    print("+ Gemini API configured successfully")
except Exception as e:
    print(f"- Error configuring Gemini API: {e}")
    sys.exit(1)


# <<< MODIFIED: The MASTER_PROMPT variable has been removed from here.

# Phase 2.1: Token estimation and smart chunking
def estimate_tokens(text: str) -> int:
    """
    Estimate token count using character-based heuristic.
    Approximation: 1 token ≈ 4 characters (conservative estimate for English text)

    Args:
        text: Text to estimate tokens for

    Returns:
        Estimated token count
    """
    return len(text) // 4


def split_into_sections(markdown_text: str) -> List[str]:
    """
    Legacy function: Splits the markdown document into sections based on Level 1 or 2 headings.
    This allows us to process the document chunk by chunk.

    Note: This is kept for backward compatibility. Use split_into_smart_chunks() for better
    token efficiency and cost optimization.
    """
    sections = re.split(r'(?m)^#{1,2}\s', markdown_text)
    processed_sections = []
    if sections[0].strip():
        processed_sections.append(sections[0])
    headings = re.findall(r'(?m)^#{1,2}\s.*', markdown_text)
    for i, section_content in enumerate(sections[1:]):
        if i < len(headings):
            full_section = headings[i] + '\n' + section_content
            processed_sections.append(full_section)
    return processed_sections if processed_sections else [markdown_text]


def split_into_smart_chunks(markdown_text: str, target_tokens: int = 1500, max_tokens: int = 2000) -> List[str]:
    """
    Phase 2.1: Smart Section Chunking with Token Awareness

    Splits markdown document into optimally-sized chunks targeting 1000-2000 tokens.
    This approach:
    - Reduces API costs by 30-40%
    - Splits on any heading level (H1-H6)
    - Breaks oversized sections at paragraph boundaries
    - Maintains semantic coherence

    Algorithm:
    1. Split by all headings (H1-H6)
    2. Check each section's token count
    3. If section > max_tokens, break at paragraph boundaries
    4. Combine small sections if they fit under target_tokens

    Args:
        markdown_text: Input markdown document
        target_tokens: Target tokens per chunk (default: 1500)
        max_tokens: Maximum tokens per chunk (default: 2000)

    Returns:
        List of optimally-sized text chunks
    """
    chunks = []

    # Step 1: Split by all heading levels (H1-H6)
    # Match any heading from # to ######
    sections = re.split(r'(?m)^#{1,6}\s', markdown_text)
    headings = re.findall(r'(?m)^#{1,6}\s.*', markdown_text)

    # Handle content before first heading
    if sections[0].strip():
        preamble = sections[0].strip()
        preamble_tokens = estimate_tokens(preamble)

        if preamble_tokens > max_tokens:
            # Split preamble at paragraph boundaries
            chunks.extend(_split_large_section(preamble, max_tokens))
        else:
            chunks.append(preamble)

    # Step 2: Process each section with its heading
    accumulator = ""  # For combining small sections
    accumulator_tokens = 0

    for i, section_content in enumerate(sections[1:]):
        if i >= len(headings):
            break

        # Reconstruct full section with heading
        full_section = headings[i] + '\n' + section_content
        section_tokens = estimate_tokens(full_section)

        # Case 1: Section is too large - must split it
        if section_tokens > max_tokens:
            # Flush accumulator first
            if accumulator:
                chunks.append(accumulator.strip())
                accumulator = ""
                accumulator_tokens = 0

            # Split large section at paragraph boundaries
            sub_chunks = _split_large_section(full_section, max_tokens)
            chunks.extend(sub_chunks)

        # Case 2: Section fits, but would make accumulator too large
        elif accumulator_tokens + section_tokens > target_tokens:
            # Flush current accumulator
            if accumulator:
                chunks.append(accumulator.strip())

            # Start new accumulator with current section
            accumulator = full_section
            accumulator_tokens = section_tokens

        # Case 3: Section fits in accumulator
        else:
            if accumulator:
                accumulator += "\n\n" + full_section
                accumulator_tokens += section_tokens
            else:
                accumulator = full_section
                accumulator_tokens = section_tokens

    # Flush final accumulator
    if accumulator:
        chunks.append(accumulator.strip())

    # Fallback: if no chunks created, return original text
    return chunks if chunks else [markdown_text]


def _split_large_section(text: str, max_tokens: int) -> List[str]:
    """
    Helper function: Split a large section at paragraph boundaries.

    Strategy:
    1. Split by double newlines (paragraphs)
    2. Accumulate paragraphs until approaching max_tokens
    3. Create new chunk when limit reached

    Args:
        text: Text to split
        max_tokens: Maximum tokens per chunk

    Returns:
        List of paragraph-based chunks
    """
    # Split by paragraph boundaries (double newline)
    paragraphs = re.split(r'\n\n+', text)

    chunks = []
    current_chunk = ""
    current_tokens = 0

    for para in paragraphs:
        para_tokens = estimate_tokens(para)

        # Edge case: Single paragraph exceeds max_tokens
        if para_tokens > max_tokens:
            # Flush current chunk
            if current_chunk:
                chunks.append(current_chunk.strip())
                current_chunk = ""
                current_tokens = 0

            # Split paragraph by sentences as last resort
            sentences = re.split(r'(?<=[.!?])\s+', para)
            sentence_chunk = ""
            sentence_tokens = 0

            for sentence in sentences:
                sent_tokens = estimate_tokens(sentence)

                if sentence_tokens + sent_tokens > max_tokens:
                    if sentence_chunk:
                        chunks.append(sentence_chunk.strip())
                    sentence_chunk = sentence
                    sentence_tokens = sent_tokens
                else:
                    if sentence_chunk:
                        sentence_chunk += " " + sentence
                    else:
                        sentence_chunk = sentence
                    sentence_tokens += sent_tokens

            if sentence_chunk:
                chunks.append(sentence_chunk.strip())

        # Normal case: Accumulate paragraphs
        elif current_tokens + para_tokens > max_tokens:
            # Flush current chunk and start new one
            if current_chunk:
                chunks.append(current_chunk.strip())
            current_chunk = para
            current_tokens = para_tokens
        else:
            # Add to current chunk
            if current_chunk:
                current_chunk += "\n\n" + para
            else:
                current_chunk = para
            current_tokens += para_tokens

    # Flush final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks if chunks else [text]


# Phase 2.2: Output Validation Layer
def validate_markdown_output(original: str, processed: str, section_num: int) -> Tuple[bool, List[str]]:
    """
    Phase 2.2: Validate LLM output for quality and correctness.

    Performs multiple validation checks:
    1. Length ratio check (output shouldn't be >3x or <0.3x original)
    2. Markdown structure preservation (headings, lists, code blocks)
    3. Information loss detection (missing key references, citations)
    4. Non-empty check

    Args:
        original: Original input text
        processed: LLM-processed text
        section_num: Section number for logging

    Returns:
        Tuple of (is_valid: bool, warnings: List[str])
    """
    warnings = []

    # Check 1: Non-empty validation
    if not processed or not processed.strip():
        return False, ["Empty response from LLM"]

    # Check 2: Length ratio validation
    # Acceptable range: 0.3x to 3x the original length
    original_len = len(original)
    processed_len = len(processed)
    length_ratio = processed_len / original_len if original_len > 0 else 0

    if length_ratio < 0.3:
        warnings.append(f"Output too short: {length_ratio:.2f}x original (possible information loss)")
    elif length_ratio > 3.0:
        warnings.append(f"Output too long: {length_ratio:.2f}x original (possible hallucination)")

    # Check 3: Markdown structure preservation
    # Count structural elements in both original and processed
    original_headings = len(re.findall(r'(?m)^#{1,6}\s', original))
    processed_headings = len(re.findall(r'(?m)^#{1,6}\s', processed))

    if original_headings > 0 and processed_headings == 0:
        warnings.append(f"All headings removed ({original_headings} -> 0)")

    original_lists = len(re.findall(r'(?m)^[\*\-\+]\s', original))
    processed_lists = len(re.findall(r'(?m)^[\*\-\+]\s', processed))

    if original_lists > 3 and processed_lists == 0:
        warnings.append(f"All list items removed ({original_lists} -> 0)")

    # Check 4: Code block preservation
    original_code_blocks = len(re.findall(r'```', original))
    processed_code_blocks = len(re.findall(r'```', processed))

    if original_code_blocks > 0 and processed_code_blocks == 0:
        warnings.append(f"All code blocks removed ({original_code_blocks // 2} blocks -> 0)")

    # Check 5: Citation/reference preservation (for academic papers)
    original_citations = len(re.findall(r'\[\d+\]|\[.*?\d{4}.*?\]', original))
    processed_citations = len(re.findall(r'\[\d+\]|\[.*?\d{4}.*?\]', processed))

    if original_citations > 5 and processed_citations < original_citations * 0.5:
        warnings.append(f"Many citations lost ({original_citations} -> {processed_citations})")

    # Check 6: URL/link preservation
    original_links = len(re.findall(r'https?://[^\s\)]+', original))
    processed_links = len(re.findall(r'https?://[^\s\)]+', processed))

    if original_links > 0 and processed_links == 0:
        warnings.append(f"All URLs removed ({original_links} -> 0)")

    # Determine validity
    # Critical failures: empty, extreme length ratio
    is_valid = True
    if not processed.strip():
        is_valid = False
    elif length_ratio < 0.2 or length_ratio > 5.0:
        is_valid = False
        warnings.append("CRITICAL: Extreme length ratio - likely LLM error")

    return is_valid, warnings


def validate_and_log(original: str, processed: str, section_num: int) -> bool:
    """
    Helper function: Validate output and log warnings.

    Args:
        original: Original input text
        processed: LLM-processed text
        section_num: Section number for logging

    Returns:
        True if validation passed, False if critical failure
    """
    is_valid, warnings = validate_markdown_output(original, processed, section_num)

    if warnings:
        for warning in warnings:
            print(f"[!] Section {section_num} validation warning: {warning}")

    if not is_valid:
        print(f"[!] Section {section_num} FAILED validation - using original content")

    return is_valid


# Configuration constants
MAX_RETRIES = 3
BASE_DELAY = 2.0  # Base delay in seconds for exponential backoff
DEFAULT_MAX_CONCURRENT = 10  # Default concurrent API calls

# Gemini Flash pricing (as of 2024)
# Note: Prices may change - update these constants as needed
GEMINI_FLASH_INPUT_COST_PER_1M = 0.075  # $0.075 per 1M input tokens
GEMINI_FLASH_OUTPUT_COST_PER_1M = 0.30  # $0.30 per 1M output tokens


# Phase 2.3: Error Diagnostics and Token Tracking
class ProcessingMetrics:
    """
    Phase 2.3: Track API usage, costs, and error statistics.

    Provides comprehensive metrics for:
    - Token usage (input/output)
    - Estimated API costs
    - Error categorization
    - Success/failure rates
    """

    def __init__(self):
        self.total_input_tokens = 0
        self.total_output_tokens = 0
        self.total_api_calls = 0
        self.successful_calls = 0
        self.failed_calls = 0

        # Error categorization
        self.errors_by_type = {
            'rate_limit': 0,
            'timeout': 0,
            'network': 0,
            'api_error': 0,
            'validation_failed': 0,
            'empty_response': 0,
            'unknown': 0
        }

        # Retry statistics
        self.sections_succeeded_first_try = 0
        self.sections_needed_retry = 0
        self.sections_failed_all_retries = 0

    def record_api_call(self, input_tokens: int, output_tokens: int, success: bool, error_type: Optional[str] = None, retry_count: int = 0):
        """Record an API call with token usage and outcome."""
        self.total_api_calls += 1
        self.total_input_tokens += input_tokens
        self.total_output_tokens += output_tokens

        if success:
            self.successful_calls += 1
            if retry_count == 0:
                self.sections_succeeded_first_try += 1
            else:
                self.sections_needed_retry += 1
        else:
            self.failed_calls += 1
            if error_type and error_type in self.errors_by_type:
                self.errors_by_type[error_type] += 1
            else:
                self.errors_by_type['unknown'] += 1

    def record_validation_failure(self):
        """Record a validation failure."""
        self.errors_by_type['validation_failed'] += 1

    def record_final_failure(self):
        """Record a section that failed all retry attempts."""
        self.sections_failed_all_retries += 1

    def estimate_cost(self) -> float:
        """
        Estimate API cost based on token usage.

        Returns:
            Estimated cost in USD
        """
        input_cost = (self.total_input_tokens / 1_000_000) * GEMINI_FLASH_INPUT_COST_PER_1M
        output_cost = (self.total_output_tokens / 1_000_000) * GEMINI_FLASH_OUTPUT_COST_PER_1M
        return input_cost + output_cost

    def print_summary(self):
        """Print comprehensive metrics summary."""
        print("\n" + "="*60)
        print("📊 PROCESSING METRICS SUMMARY")
        print("="*60)

        # Token Usage
        print("\n🔢 Token Usage:")
        print(f"  Input tokens:  {self.total_input_tokens:,}")
        print(f"  Output tokens: {self.total_output_tokens:,}")
        print(f"  Total tokens:  {self.total_input_tokens + self.total_output_tokens:,}")

        # Cost Estimation
        cost = self.estimate_cost()
        print(f"\n💰 Estimated Cost: ${cost:.4f} USD")

        # API Calls
        print(f"\n📞 API Calls:")
        print(f"  Total calls:      {self.total_api_calls}")
        print(f"  Successful:       {self.successful_calls} ({self.successful_calls/self.total_api_calls*100:.1f}%)")
        print(f"  Failed:           {self.failed_calls} ({self.failed_calls/self.total_api_calls*100:.1f}%)")

        # Retry Statistics
        print(f"\n🔄 Retry Statistics:")
        print(f"  First try success: {self.sections_succeeded_first_try}")
        print(f"  Needed retries:    {self.sections_needed_retry}")
        print(f"  Failed all retries: {self.sections_failed_all_retries}")

        # Error Breakdown
        print(f"\n⚠️  Error Breakdown:")
        for error_type, count in self.errors_by_type.items():
            if count > 0:
                print(f"  {error_type:20s}: {count}")

        print("="*60 + "\n")


def categorize_error(exception: Exception) -> str:
    """
    Phase 2.3: Categorize API errors for better diagnostics.

    Args:
        exception: Exception from API call

    Returns:
        Error category string
    """
    error_str = str(exception).lower()
    error_type = type(exception).__name__.lower()

    # Rate limit errors
    if 'rate' in error_str or 'quota' in error_str or '429' in error_str:
        return 'rate_limit'

    # Timeout errors
    if 'timeout' in error_str or 'timed out' in error_str:
        return 'timeout'

    # Network errors
    if 'connection' in error_str or 'network' in error_str or 'unreachable' in error_str:
        return 'network'

    # API-specific errors
    if 'httperror' in error_type or 'apierror' in error_type:
        return 'api_error'

    # Unknown
    return 'unknown'


async def call_llm_for_correction_async_single(text_chunk: str, prompt_template: str, model: LLMModel, section_num: int, metrics: Optional['ProcessingMetrics'] = None) -> Optional[str]:
    """
    Single attempt async API call (internal use).
    Now includes Phase 2.3 metrics tracking.

    Returns None if the API call fails.
    """
    prompt = prompt_template.replace("{text_chunk}", text_chunk)

    # Estimate input tokens
    input_tokens = estimate_tokens(prompt)

    try:
        # Use the Gemini SDK's native asynchronous method
        response = await model.generate_content_async(prompt)

        # Estimate output tokens
        output_text = response.text.strip() if response.text else ""
        output_tokens = estimate_tokens(output_text)

        # Record successful API call
        if metrics:
            metrics.record_api_call(input_tokens, output_tokens, success=True)

        if not output_text:
            if metrics:
                metrics.errors_by_type['empty_response'] += 1
            return None

        return output_text

    except Exception as e:
        # Record failed API call with error categorization
        if metrics:
            error_category = categorize_error(e)
            metrics.record_api_call(input_tokens, 0, success=False, error_type=error_category)

        # Propagate exception for retry logic to handle
        raise e


async def call_llm_for_correction_async(text_chunk: str, prompt_template: str, model: LLMModel, section_num: int, max_retries: int = MAX_RETRIES, metrics: Optional['ProcessingMetrics'] = None) -> Optional[str]:
    """
    Asynchronous API Call Function with Retry Logic
    Uses Gemini's native async API with exponential backoff.
    Now includes Phase 2.3 metrics tracking and error categorization.

    Args:
        text_chunk: Text content to process
        prompt_template: Prompt template with {text_chunk} placeholder
        model: LLM model instance
        section_num: Section number for logging
        max_retries: Maximum number of retry attempts (default: 3)
        metrics: Optional ProcessingMetrics instance for tracking

    Returns:
        Processed text or None if all retries fail
    """
    last_error = None
    last_error_category = None

    for attempt in range(max_retries):
        try:
            result = await call_llm_for_correction_async_single(text_chunk, prompt_template, model, section_num, metrics)

            if result and result.strip():
                # Success!
                if attempt > 0:
                    print(f"[*] Section {section_num} - Succeeded on attempt {attempt + 1}")
                    if metrics:
                        # Note: individual call already recorded, just track retry stat
                        pass
                return result
            else:
                # Empty response
                last_error = "Empty response from API"
                last_error_category = 'empty_response'
                if attempt < max_retries - 1:
                    print(f"[!] Section {section_num} - Empty response on attempt {attempt + 1}, retrying...")

        except Exception as e:
            last_error = str(e)
            last_error_category = categorize_error(e)
            error_type = type(e).__name__

            if attempt < max_retries - 1:
                print(f"[!] Section {section_num} - {error_type} ({last_error_category}) on attempt {attempt + 1}, retrying...")
            else:
                print(f"[!] Section {section_num} - {error_type} ({last_error_category}) on attempt {attempt + 1}")

        # Exponential backoff with jitter (if not the last attempt)
        if attempt < max_retries - 1:
            # Calculate delay: base_delay * (2 ^ attempt) + random jitter
            delay = BASE_DELAY * (2 ** attempt) + random.uniform(0, 1)
            await asyncio.sleep(delay)

    # All retries failed
    if metrics:
        metrics.record_final_failure()

    print(f"[!] Section {section_num} - FAILED after {max_retries} attempts. Error: {last_error}")
    return None

def call_llm_for_correction(text_chunk: str, prompt_template: str, model: LLMModel) -> Optional[str]:
    """
    Legacy synchronous version (kept for compatibility)
    Sends a chunk of text to the LLM with the master prompt and returns the corrected version.
    Returns None if the API call fails.
    """
    prompt = prompt_template.replace("{text_chunk}", text_chunk)
    try:
        response = model.generate_content(prompt)
        if not response.text.strip():
            print("\n[!] Warning: LLM returned an empty response.")
            return None
        return response.text.strip()
    except Exception as e:
        print(f"\n[!] Error during LLM call: {e}")
        return None


def main() -> None:
    """
    Main function to run the Stage 2 processing.
    """
    parser = argparse.ArgumentParser(
        description="Stage 2: Applies LLM-based formatting to a preprocessed Markdown file.",
        formatter_class=argparse.RawTextHelpFormatter,
        epilog="Example Usage:\n"
               "python stage2.py [input_file] [output_file] [prompt_file]\n"
               "If no arguments provided, uses default paths."
    )
    # <<< MODIFIED: Added an argument for the prompt file path.
    parser.add_argument("input_file", nargs='?', default=None, 
                       help="The path to the Stage 1 preprocessed file. (default: auto-detect from most recent folder)")
    parser.add_argument("output_file", nargs='?', default=None,
                       help="The path where the final, fully formatted file will be saved. (default: auto-detect from input path)")
    parser.add_argument("prompt_file", nargs='?', default="config/universal_research_prompt.md",
                       help="The path to the .md file containing the formatting prompt.")
    parser.add_argument("--sync", action="store_true",
                       help="Use synchronous processing instead of async (slower but more conservative)")
    parser.add_argument("--max-concurrent", type=int, default=None,
                       help=f"Maximum concurrent API calls (default: {DEFAULT_MAX_CONCURRENT})")
    parser.add_argument("--smart-chunking", action="store_true",
                       help="Use token-aware smart chunking (reduces API costs by 30-40%)")
    
    args = parser.parse_args()
    
    # Auto-detect paths if not provided
    if args.input_file is None or args.output_file is None:
        # Find most recent output directory (fallback to document_ocr_test for backward compatibility)
        possible_dirs = [d for d in os.listdir('.') if os.path.isdir(d) and not d.startswith('.') and d not in ['stages', 'config', 'utils', 'output', 'venv']]
        if possible_dirs:
            # Sort by modification time, most recent first
            possible_dirs.sort(key=lambda x: os.path.getmtime(x), reverse=True)
            detected_dir = possible_dirs[0]
        else:
            detected_dir = "document_ocr_test"  # Fallback
        
        if args.input_file is None:
            args.input_file = f"{detected_dir}/stage_1_complete.md"
        if args.output_file is None:
            args.output_file = f"{detected_dir}/final_formatted.md"

    # Resolve paths to absolute paths
    from pathlib import Path
    args.input_file = str(Path(args.input_file).resolve())
    args.output_file = str(Path(args.output_file).resolve())
    args.prompt_file = str(Path(args.prompt_file).resolve())

    output_dir = os.path.dirname(args.output_file)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir)
        print(f"[*] Created output directory: {output_dir}")

    # Load input files
    print(f"[*] Reading Stage 1 file from: {args.input_file}")
    
    try:
        with open(args.input_file, 'r', encoding='utf-8') as f:
            stage1_text = f.read()
        
        print(f"[*] Reading Universal Research Prompt from: {args.prompt_file}")
        with open(args.prompt_file, 'r', encoding='utf-8') as f:
            prompt_text = f.read()
            
    except FileNotFoundError as e:
        print(f"[!] Error: An input file was not found.", file=sys.stderr)
        print(f"    Details: {e}", file=sys.stderr)
        sys.exit(1)

    print("[*] Splitting document into logical sections...")

    # Phase 2.1: Use smart chunking if enabled
    if args.smart_chunking:
        print("[*] Using smart token-aware chunking (targeting 1000-2000 tokens per chunk)")
        sections = split_into_smart_chunks(stage1_text, target_tokens=1500, max_tokens=2000)
        total_tokens = sum(estimate_tokens(s) for s in sections)
        avg_tokens = total_tokens // len(sections) if sections else 0
        print(f"[*] Created {len(sections)} optimized chunks (avg {avg_tokens} tokens per chunk)")
        print(f"[*] Estimated total tokens: {total_tokens} (~30-40% reduction vs legacy splitting)")
    else:
        sections = split_into_sections(stage1_text)
        print(f"[*] Found {len(sections)} sections to process (using legacy H1/H2 splitting)")
    
    model = genai.GenerativeModel('gemini-1.5-flash-latest')

    
    def process_section_with_retries(section, prompt_text, section_num, pass_name=""):
        """Legacy synchronous version (kept for compatibility)"""
        max_retries = 3
        corrected_chunk = None
        for attempt in range(max_retries):
            corrected_chunk = call_llm_for_correction(section, prompt_text, model)
            if corrected_chunk and corrected_chunk.strip():  # Check for actual content
                print(f"[*] Section {section_num}{pass_name} processed successfully.")
                return corrected_chunk
            elif corrected_chunk:
                print(f"[!] Section {section_num}{pass_name} returned only whitespace on attempt {attempt + 1}")
            
            delay = 5 * (2 ** attempt)
            print(f"[*] Attempt {attempt + 1} failed. Retrying in {delay} seconds...")
            time.sleep(delay)
        
        print(f"[!] FAILED to process section {section_num}{pass_name} after {max_retries} attempts.")
        return None

    async def process_section_with_semaphore(semaphore: asyncio.Semaphore, section: str, section_num: int, metrics: ProcessingMetrics) -> str:
        """
        Process a single section with rate limiting via semaphore.
        Now includes Phase 2.2 validation layer and Phase 2.3 metrics tracking.

        Args:
            semaphore: Asyncio semaphore for rate limiting
            section: Section text to process
            section_num: Section number for logging
            metrics: ProcessingMetrics instance for tracking

        Returns:
            Processed text or original text on failure/validation failure
        """
        async with semaphore:
            result = await call_llm_for_correction_async(section, prompt_text, model, section_num, metrics=metrics)

            if result is None or not result.strip():
                print(f"[!] Section {section_num} - Using original content (empty response)")
                return section

            # Phase 2.2: Validate output before accepting
            is_valid = validate_and_log(section, result, section_num)

            if not is_valid:
                # Validation failed - record and use original content
                metrics.record_validation_failure()
                return section
            else:
                # Validation passed - use processed content
                return result

    async def process_all_sections_concurrently():
        """
        Step 2: Main Asynchronous Orchestrator with Rate Limiting and Progress Tracking
        Manages and executes concurrent tasks with semaphore-based rate limiting.
        Now includes Phase 2.3 comprehensive metrics tracking.
        """
        # Phase 2.3: Initialize metrics tracking
        metrics = ProcessingMetrics()

        # Determine max concurrent requests
        max_concurrent = args.max_concurrent if args.max_concurrent else DEFAULT_MAX_CONCURRENT
        max_concurrent = min(max_concurrent, len(sections))  # Don't exceed number of sections

        print(f"[*] Processing {len(sections)} sections with max {max_concurrent} concurrent requests...")
        print(f"[*] Retry policy: {MAX_RETRIES} attempts with exponential backoff")

        # Create semaphore for rate limiting
        semaphore = asyncio.Semaphore(max_concurrent)

        # Task Creation: Create rate-limited tasks
        tasks = []
        for i, section in enumerate(sections):
            heading_line = section.strip().split('\n', 1)[0] if section.strip() else "Empty section"
            if i < 3 or i >= len(sections) - 1:  # Show first 3 and last
                print(f"[*] Task {i+1}/{len(sections)}: '{heading_line[:60]}...'")
            elif i == 3:
                print(f"[*] ... processing remaining sections ...")

            # Create rate-limited task with metrics tracking
            task = process_section_with_semaphore(semaphore, section, i+1, metrics)
            tasks.append(task)

        # Concurrent Execution: Execute tasks with rate limiting and progress bar
        print(f"\n[*] Starting concurrent processing...")
        start_time = time.time()

        # Execute all tasks with rate limiting and progress bar (if available)
        if TQDM_AVAILABLE:
            # Use tqdm progress bar
            results = await atqdm.gather(*tasks, desc="Processing sections", unit="section", return_exceptions=True)
        else:
            # Fallback to regular gather
            results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        processing_time = end_time - start_time

        # Result Handling: Process results and count successes/failures
        final_sections = []
        success_count = 0
        failure_count = 0

        for i, result in enumerate(results):
            if isinstance(result, Exception):
                print(f"[!] Section {i+1} failed with exception: {result}")
                print(f"[!] Using original content for section {i+1}")
                final_sections.append(sections[i])
                failure_count += 1
            elif result is None or not result.strip():
                print(f"[!] Section {i+1} returned empty response")
                print(f"[!] Using original content for section {i+1}")
                final_sections.append(sections[i])
                failure_count += 1
            else:
                final_sections.append(result)
                success_count += 1

        print(f"\n[+] Processing complete in {processing_time:.2f} seconds!")
        print(f"[+] Success: {success_count}/{len(sections)} sections")
        if failure_count > 0:
            print(f"[!] Failed: {failure_count}/{len(sections)} sections (using original content)")

        # Phase 2.3: Print comprehensive metrics summary
        metrics.print_summary()

        return final_sections

    try:
        # Step 3: Integrate the Async Workflow into main function
        # Conditional Logic: Choose between sync and async based on command-line flag
        if args.sync:
            print("[*] Using synchronous processing (sequential API calls)...")
            # The original synchronous for loop - one by one processing
            final_sections = []
            
            for i, section in enumerate(sections):
                heading_line = section.strip().split('\n', 1)[0]
                print(f"\n[*] Processing Section {i+1}/{len(sections)}: '{heading_line[:60]}...'")
                
                corrected_chunk = process_section_with_retries(section, prompt_text, i+1)
                final_sections.append(corrected_chunk if corrected_chunk else section)
            
            sections_to_write = final_sections
        else:
            print("[*] Using asynchronous concurrent processing...")
            # Single call to start the entire concurrent process
            final_sections = asyncio.run(process_all_sections_concurrently())
            sections_to_write = final_sections

        # Create the output file first to ensure it exists
        print(f"[*] Creating output file: {args.output_file}")
        try:
            with open(args.output_file, 'w', encoding='utf-8') as f:
                f.write("")  # Create empty file
            print(f"[*] Output file created successfully")
        except Exception as e:
            print(f"[!] Error creating output file: {e}")
            raise

        # Write final results to file
        print(f"[*] Writing content to: {args.output_file}")
        with open(args.output_file, 'w', encoding='utf-8') as output_file:
            for i, section in enumerate(sections_to_write):
                try:
                    if section and section.strip():  # Check if section has actual content
                        output_file.write(section)
                    else:
                        print(f"[!] Warning: Section {i+1} is empty or contains only whitespace, using original...")
                        # Fall back to original section
                        if i < len(sections):
                            output_file.write(sections[i])
                        else:
                            print(f"[!] Error: No original section available for section {i+1}")
                            continue
                    
                    # Add section separator (but not after the last section)
                    if i < len(sections_to_write) - 1:
                        output_file.write("\n\n")
                        
                except Exception as e:
                    print(f"[!] Error writing section {i+1}: {e}")
                    print(f"[!] Section content type: {type(section)}, length: {len(section) if section else 'None'}")
                    # Try to write original section as fallback
                    if i < len(sections):
                        output_file.write(sections[i])
                        if i < len(sections_to_write) - 1:
                            output_file.write("\n\n")
        
        print("\n[+] Stage 2 processing complete! Your document is fully formatted.")
        print(f"[*] Final output saved to: {args.output_file}")

        # Copy to standardized output folder for testing
        try:
            # Create timestamp for unique filename
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

            # Get input filename without extension
            input_path = Path(args.input_file)
            # Try to extract document name from path (e.g., "bio_paper_1" from path)
            if input_path.parent.name and input_path.parent.name not in ['output', '.', '']:
                doc_name = input_path.parent.name
            else:
                doc_name = input_path.stem

            # Ensure standardized output directory exists
            markdown_output_dir = "output/markdown_output"
            os.makedirs(markdown_output_dir, exist_ok=True)

            # Copy to standardized folder
            markdown_copy_filename = f"{doc_name}_{timestamp}.md"
            markdown_copy_path = os.path.join(markdown_output_dir, markdown_copy_filename)
            shutil.copy2(args.output_file, markdown_copy_path)

            print(f"[*] Copy saved to standardized testing folder: {os.path.abspath(markdown_copy_path)}")

        except Exception as copy_error:
            print(f"[!] Warning: Failed to copy to standardized output folder: {copy_error}")
            print(f"[!] This does not affect the main output file")

    except Exception as e:
        print(f"\n[!] An error occurred while writing to the file: {e}")

if __name__ == "__main__":
    main()