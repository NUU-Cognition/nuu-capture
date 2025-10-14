# Stage 2 (LLM Formatting) - Detailed Technical Breakdown

## Overview

**Purpose**: Apply advanced LLM-based formatting to preprocessed markdown using Google Gemini API.

**Location**: `stages/03_format/stage2.py`

**Model Used**: `gemini-1.5-flash-latest`

**Processing Strategy**: Section-by-section concurrent or sequential processing

---

## Architecture Components

### 1. **Configuration & Setup** (Lines 1-28)

```python
# Dependencies
- google.generativeai (Gemini SDK)
- asyncio (for concurrent processing)
- dotenv (environment variables)

# API Configuration
- Loads GEMINI_API_KEY from .env
- Configures Gemini SDK at module level
- Exits immediately if API key missing
```

**Design Decision**: Early exit on missing API key prevents wasted processing time.

---

### 2. **Section Splitting Logic** (Lines 33-47)

**Function**: `split_into_sections(markdown_text: str) -> List[str]`

**Algorithm**:
```python
1. Split text by Level 1-2 headings (# or ##)
2. Extract all headings separately
3. Reconstruct sections by prepending heading to content
4. Handle edge case: content before first heading
```

**Regex Pattern**: `r'(?m)^#{1,2}\s'`
- `(?m)`: Multiline mode
- `^`: Start of line
- `#{1,2}`: One or two hash symbols
- `\s`: Whitespace

**Example Flow**:
```
Input:
# Introduction
Content here

## Methods
More content

Output:
[
  "# Introduction\nContent here",
  "## Methods\nMore content"
]
```

**Strengths**:
- Clean separation of sections
- Preserves heading hierarchy
- Handles documents without headings

**Limitations**:
- Only splits on H1/H2 (ignores H3-H6)
- May create very large sections if few headings
- No size-based splitting logic

---

### 3. **LLM Call Functions** (Lines 51-84)

#### **Async Version** (Primary)

```python
async def call_llm_for_correction_async(
    text_chunk: str,
    prompt_template: str,
    model: LLMModel,
    section_num: int
) -> Optional[str]
```

**Flow**:
```
1. Replace {text_chunk} placeholder in prompt
2. Call model.generate_content_async(prompt)
3. Check if response is empty
4. Return text or None on failure
```

**Error Handling**:
- Catches all exceptions
- Returns None on failure (not exception)
- Logs section number for debugging

**Performance**: True concurrency via async/await

---

#### **Sync Version** (Legacy)

```python
def call_llm_for_correction(
    text_chunk: str,
    prompt_template: str,
    model: LLMModel
) -> Optional[str]
```

**Differences from Async**:
- Synchronous API call
- No section number tracking
- Kept for backward compatibility
- Used in retry logic

---

### 4. **Processing Modes** (Lines 162-225)

#### **Mode A: Synchronous Processing** (`--sync` flag)

**Function**: `process_section_with_retries()`

**Algorithm**:
```python
for attempt in [0, 1, 2]:  # 3 attempts
    result = call_llm_for_correction(section, prompt, model)
    if result and result.strip():
        return result

    # Exponential backoff
    delay = 5 * (2 ** attempt)  # 5s, 10s, 20s
    sleep(delay)

return None  # All retries failed
```

**Characteristics**:
- **Sequential**: One section at a time
- **Retry Logic**: 3 attempts per section
- **Exponential Backoff**: 5s → 10s → 20s delays
- **Fallback**: Uses original content on total failure

**Pros**:
- Reliable and conservative
- Better error recovery
- Lower API rate limit risk

**Cons**:
- Very slow for large documents
- No parallelization
- Long total processing time

**Time Complexity**: `O(n * retries * api_time)`
- 10 sections × 3 retries × 3s = up to 90 seconds per section

---

#### **Mode B: Asynchronous Processing** (Default)

**Function**: `process_all_sections_concurrently()`

**Algorithm**:
```python
# Step 1: Create all tasks
tasks = [
    call_llm_for_correction_async(section, prompt, model, i)
    for i, section in enumerate(sections)
]

# Step 2: Execute ALL tasks concurrently
results = await asyncio.gather(*tasks, return_exceptions=True)

# Step 3: Handle results
for i, result in enumerate(results):
    if isinstance(result, Exception):
        use_original_content()
    elif not result or not result.strip():
        use_original_content()
    else:
        use_processed_content()
```

**Characteristics**:
- **Concurrent**: All sections processed simultaneously
- **Single-Pass**: No retry logic (!)
- **Exception Handling**: `return_exceptions=True` prevents cascade failures
- **Fallback**: Uses original content on failure

**Pros**:
- Extremely fast for multiple sections
- Optimal API utilization
- Clean async/await pattern

**Cons**:
- **No retry logic** - single attempt per section
- Higher failure rate on API issues
- No rate limiting control
- All-or-nothing approach

**Time Complexity**: `O(max(api_times))` ≈ 3-10 seconds total
- 50 sections processed in ~10 seconds vs 2+ minutes

---

### 5. **Main Processing Pipeline** (Lines 87-293)

**Workflow**:

```
1. Argument Parsing
   ├─ input_file (auto-detect or specified)
   ├─ output_file (auto-detect or specified)
   ├─ prompt_file (default: config/universal_research_prompt.md)
   ├─ --sync flag (optional)
   └─ --max-concurrent (unused in current implementation!)

2. Path Resolution
   ├─ Auto-detect most recent output directory
   ├─ Fallback to "document_ocr_test"
   └─ Resolve all paths to absolute

3. File Loading
   ├─ Read input markdown
   ├─ Read prompt template
   └─ Exit on FileNotFoundError

4. Section Splitting
   └─ split_into_sections(stage1_text)

5. Model Initialization
   └─ genai.GenerativeModel('gemini-1.5-flash-latest')

6. Processing Selection
   ├─ if --sync:
   │   └─ Sequential with retries
   └─ else:
       └─ Concurrent (no retries)

7. Output Writing
   ├─ Create output file
   ├─ Write each section with \n\n separator
   └─ Handle write errors per-section
```

---

## Data Flow Diagram

```
Input: stage_1_complete.md
         ↓
    [Split by H1/H2]
         ↓
    List of Sections
         ↓
    ┌──────────────┐
    │   Choose     │
    │   Mode       │
    └──────┬───────┘
           │
    ┌──────┴────────┐
    │               │
 [SYNC]          [ASYNC]
    │               │
 For each         Create
 section:         all tasks
    │               │
 Try 3x           Execute
 with             concurrently
 backoff             │
    │               │
 Return           Get all
 result           results
    │               │
    └───────┬───────┘
            │
    Process Results
    (use original on failure)
            │
    Write to Output
            ↓
    final_formatted.md
```

---

## Current Strengths

### ✅ **1. Dual Processing Modes**
- Flexibility for different use cases
- Sync for reliability, async for speed

### ✅ **2. Graceful Degradation**
- Falls back to original content on failure
- Zero information loss guarantee maintained

### ✅ **3. Clean Section Splitting**
- Logical document segmentation
- Preserves structure

### ✅ **4. Proper Async Implementation**
- Uses native SDK async methods
- `asyncio.gather()` for true concurrency
- `return_exceptions=True` prevents cascade failures

### ✅ **5. Path Auto-Detection**
- Works with unified pipeline seamlessly
- Intelligent directory discovery

---

## Critical Limitations & Issues

### ❌ **1. NO RETRY LOGIC IN ASYNC MODE**

**Problem**: Async mode makes single attempt per section

```python
# Current: No retries
results = await asyncio.gather(*tasks, return_exceptions=True)

# Missing: Retry logic for failed sections
```

**Impact**:
- High failure rate on transient API errors
- Network hiccups cause permanent failures
- Rate limit errors not handled

**Recommendation**: Implement async retry with exponential backoff

---

### ❌ **2. UNUSED `--max-concurrent` ARGUMENT**

**Problem**: Argument defined but never used

```python
parser.add_argument("--max-concurrent", type=int, default=None,
                   help="Maximum concurrent API calls...")
# ⚠️ Never referenced in code!
```

**Impact**:
- May exceed API rate limits
- No control over concurrency level
- Could cause billing spikes

**Recommendation**: Implement semaphore-based rate limiting

---

### ❌ **3. FIXED MODEL SELECTION**

**Problem**: Hardcoded model name

```python
model = genai.GenerativeModel('gemini-1.5-flash-latest')
# No way to change model without code modification
```

**Impact**:
- Can't A/B test different models
- Can't use more powerful models for complex documents
- No flexibility for cost optimization

**Recommendation**: Add `--model` argument

---

### ❌ **4. NO PROGRESS TRACKING**

**Problem**: No visual feedback during processing

**What's Missing**:
- Progress bar for async processing
- Section completion percentage
- Estimated time remaining
- Success/failure counters

**Impact**:
- User doesn't know if process is frozen
- Can't estimate completion time
- No visibility into failures

**Recommendation**: Add `tqdm` progress bar

---

### ❌ **5. NO TOKEN/COST TRACKING**

**Problem**: No awareness of API usage

**Missing Metrics**:
- Input token count
- Output token count
- Estimated API cost
- Rate limit proximity

**Impact**:
- Unexpected billing
- No cost optimization
- May hit rate limits unexpectedly

**Recommendation**: Track and log token usage

---

### ❌ **6. INEFFICIENT SECTION SPLITTING**

**Problem**: Only splits on H1/H2

```python
# Current: Fixed splitting
sections = re.split(r'(?m)^#{1,2}\s', markdown_text)

# Issue: May create 20KB sections
# Issue: Ignores H3, H4, H5, H6
```

**Impact**:
- Very large sections consume more tokens
- Higher latency per API call
- More expensive processing

**Recommendation**: Implement smart chunking with size limits

---

### ❌ **7. NO VALIDATION OF LLM OUTPUT**

**Problem**: No quality checks on responses

**Missing Checks**:
- Output is still valid markdown
- Section length ratio (input vs output)
- Formatting markers preserved
- References maintained

**Impact**:
- LLM may return garbage
- Information loss undetected
- Formatting errors propagate

**Recommendation**: Add validation layer

---

### ❌ **8. POOR ERROR DIAGNOSTICS**

**Problem**: Generic error messages

```python
except Exception as e:
    print(f"[!] Error during async LLM call: {e}")
    return None
```

**Missing Information**:
- Which section failed
- What was the API error code
- How many tokens were used
- Was it a rate limit, timeout, or content filter?

**Impact**:
- Hard to debug failures
- Can't distinguish transient from permanent errors
- No actionable error recovery

---

### ❌ **9. NO CACHING**

**Problem**: Re-processes identical sections every run

**Missing Feature**:
- Cache API responses by (section_hash, model, prompt_hash)
- Skip already-processed sections
- Resume interrupted processing

**Impact**:
- Wastes money on re-processing
- Longer processing times
- Can't resume failed runs

**Recommendation**: Implement Redis or disk-based cache

---

### ❌ **10. SYNCHRONOUS PROMPT LOADING**

**Problem**: Loads prompt in main thread

```python
with open(args.prompt_file, 'r') as f:
    prompt_text = f.read()
```

**Minor Issue**: Not async, but could be optimized

---

## Performance Characteristics

### **Async Mode**
```
Document with 50 sections:
- Time: ~8-15 seconds total
- Throughput: 3-6 sections/second
- Bottleneck: API latency + network
- Cost: 50 API calls × token cost
```

### **Sync Mode**
```
Document with 50 sections:
- Time: ~150-450 seconds (2.5-7.5 min)
- Throughput: 0.1-0.3 sections/second
- Bottleneck: Sequential processing + retries
- Cost: 50-150 API calls × token cost (with retries)
```

**Speedup**: Async is **10-30x faster** than sync

---

## Token Usage Estimate

**Average Section**: ~2000 tokens input + 2200 tokens output = 4200 tokens
**50 Sections**: 50 × 4200 = 210,000 tokens
**Estimated Cost**: $0.21 - $0.42 (Gemini Flash pricing)

**Optimization Opportunity**: Reduce section sizes to save 30-40% tokens

---

## Code Quality Issues

### **1. Dead Code**
```python
args.max_concurrent  # Defined but never used
```

### **2. Inconsistent Logging**
```python
print("[*] ...")  # Some logs
print("+ ...")     # Other logs
print("[!] ...")   # Error logs
# No consistent logging framework
```

### **3. Magic Numbers**
```python
max_retries = 3
delay = 5 * (2 ** attempt)
# Should be constants or config
```

### **4. No Type Hints on Main**
```python
def main() -> None:  # ✓
def split_into_sections(text: str) -> List[str]:  # ✓
# But many internal functions lack types
```

### **5. No Unit Tests**
- No test coverage
- Can't verify refactorings
- No CI/CD integration

---

## Memory Profile

**Peak Memory Usage**:
```
- Input document: ~500KB
- Sections array: ~500KB (copies)
- Async tasks: ~50 × 10KB = 500KB (futures)
- Results array: ~600KB (processed sections)
Total: ~2-3 MB for typical document
```

**Memory Efficient**: Yes, for documents up to 10MB

---

## Recommended Improvements (Priority Order)

### 🔴 **Critical (Must Fix)**

1. **Add Retry Logic to Async Mode**
   - 3 retries per section
   - Exponential backoff with jitter
   - Separate retry queue for failed sections

2. **Implement Rate Limiting**
   - Use `--max-concurrent` argument
   - Semaphore-based concurrency control
   - Respect API rate limits

3. **Add Progress Tracking**
   - tqdm progress bar
   - Success/failure counters
   - ETA calculation

### 🟡 **High Priority (Should Fix)**

4. **Smart Section Chunking**
   - Target 1000-2000 token sections
   - Split on any heading level
   - Break large paragraphs

5. **Output Validation**
   - Markdown syntax validation
   - Length ratio checks
   - Reference preservation

6. **Better Error Handling**
   - Specific exception types
   - Actionable error messages
   - Retry/skip/abort options

### 🟢 **Medium Priority (Nice to Have)**

7. **Response Caching**
   - Hash-based cache key
   - Disk or Redis cache
   - Resume capability

8. **Token Tracking**
   - Input/output token counts
   - Cost estimation
   - Usage reporting

9. **Model Selection**
   - `--model` argument
   - Support multiple models
   - Cost/quality tradeoffs

### 🔵 **Low Priority (Future)**

10. **Structured Logging**
    - Replace print() with logging module
    - Log levels (DEBUG, INFO, WARN, ERROR)
    - Log file output

11. **Configuration File**
    - YAML config for all settings
    - Per-model prompts
    - Retry policies

12. **Unit Tests**
    - Mock API responses
    - Test retry logic
    - Test error handling

---

## Conclusion

**Current State**: Functional but fragile
- ✅ Fast async processing
- ✅ Graceful degradation
- ❌ No retry in async mode
- ❌ Poor error handling
- ❌ Limited observability

**Improvement Potential**: 🔥 **Very High**
- Could reduce failures by 80%
- Better user experience
- Cost optimization possible
- Production-ready with fixes

**Next Steps**:
1. Fix async retry logic (highest impact)
2. Add progress tracking (best UX improvement)
3. Implement rate limiting (stability)
