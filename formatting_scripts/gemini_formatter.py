import google.generativeai as genai
import os
import re
import time
import json
from dotenv import load_dotenv
from google.api_core import exceptions

# --- 1. Configuration ---
# Load environment variables from .env file
load_dotenv()

# Configure Gemini API with key from .env file
try:
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        print("❌ Error: GEMINI_API_KEY not found in .env file")
        print("Please add GEMINI_API_KEY=your_api_key to your .env file")
        exit()
    genai.configure(api_key=api_key)
    print("✅ Gemini API configured successfully")
except Exception as e:
    print(f"❌ Error configuring Gemini API: {e}")
    exit()


# --- 2. Define File Paths ---
# Ensure these paths are correct for your environment
markdown_file_path = 'saved_markdowns/processed_document.md'
# IMPORTANT: This now points to the new prompt file for the editing approach
prompt_file_path = 'formatting_prompt.txt'
# Saving to a new file to distinguish from the old method
output_file_path = 'saved_markdowns/processed_document_gemini_edited.md'


# --- 3. Read Content from Local Files ---
try:
    with open(markdown_file_path, 'r', encoding='utf-8') as f:
        markdown_content = f.read()
    print(f"✅ Successfully read '{markdown_file_path}'.")

    with open(prompt_file_path, 'r', encoding='utf-8') as f:
        prompt_text = f.read()
    print(f"✅ Successfully read '{prompt_file_path}'.")

except FileNotFoundError as e:
    print(f"❌ Error: {e}. Please ensure file paths are correct and files exist.")
    exit()


# --- 4. Chunking Function ---
def chunk_markdown_by_section(content):
    """
    Splits the markdown content into chunks based on top-level headings (e.g., '# Title').
    The heading is included with the chunk.
    """
    chunks = re.split(r'(?=^#\s)', content, flags=re.MULTILINE)
    return [chunk for chunk in chunks if chunk.strip()]


# --- 5. Process Each Chunk to Get and Apply Edits ---
print("\n⚙️  Processing document to find and apply edits...")
document_chunks = chunk_markdown_by_section(markdown_content)
print(f"   Document split into {len(document_chunks)} chunks.")

edited_chunks = []
model = genai.GenerativeModel('gemini-1.5-pro-latest')

for i, chunk in enumerate(document_chunks):
    chunk_number = i + 1
    print(f"\n   Analyzing chunk {chunk_number} of {len(document_chunks)}...")
    
    max_retries = 3
    initial_delay = 5  # seconds
    
    # Start with the original content; we will apply edits to this variable
    edited_chunk_content = chunk

    for attempt in range(max_retries):
        try:
            # Create the specific prompt for the find-and-replace task
            chunk_prompt = f"{prompt_text}\n\n---START OF CHUNK---\n\n{edited_chunk_content}\n\n---END OF CHUNK---"
            
            # Call the API to get the list of edits in JSON format
            response = model.generate_content(chunk_prompt)
            
            # --- THIS IS THE NEW CORE LOGIC ---
            try:
                # The model should return a raw JSON string. We parse it here.
                edits = json.loads(response.text)
                if not isinstance(edits, list):
                    print(f"   ⚠️  Model did not return a list of edits. Skipping edits for this chunk.")
                    break

                if edits:
                    print(f"   Found {len(edits)} edits. Applying them now...")
                    # Loop through the edits and apply them to the chunk content
                    for edit in edits:
                        original = edit.get("original")
                        replacement = edit.get("replacement")
                        if original is not None and replacement is not None:
                            edited_chunk_content = edited_chunk_content.replace(original, replacement)
                else:
                    print("   No edits found for this chunk.")

                print(f"   ✅ Chunk {chunk_number} analyzed successfully.")

            except json.JSONDecodeError:
                print(f"   ⚠️  Could not decode JSON from model response. Skipping edits for this chunk.")
            # --- END OF NEW CORE LOGIC ---

            time.sleep(2) # Proactive delay to respect rate limits
            break  # Exit the retry loop on success

        except exceptions.ResourceExhausted as e:
            delay = initial_delay * (2 ** attempt)
            print(f"   ⚠️ Rate limit hit. Retrying in {delay} seconds... (Attempt {attempt + 1}/{max_retries})")
            time.sleep(delay)

        except Exception as e:
            print(f"   ❌ An unexpected API error occurred on chunk {chunk_number}: {e}")
            break
    else:
        # This block runs if all retries failed
        print(f"   ❌ Failed to process chunk {chunk_number} after {max_retries} attempts. Using original content.")

    edited_chunks.append(edited_chunk_content)


# --- 6. Combine and Save the Final Edited Document ---
if edited_chunks:
    print("\n✅ Document editing completed!")
    final_document = "\n".join(edited_chunks)
    
    print(f"📁 Saving edited content to: {output_file_path}")
    try:
        with open(output_file_path, 'w', encoding='utf-8') as f:
            f.write(final_document)
        print("💾 Edited document saved successfully!")
        
        print(f"\n📊 Summary:")
        print(f"   Original: {len(markdown_content)} characters")
        print(f"   Edited:   {len(final_document)} characters")
        
    except Exception as e:
        print(f"❌ Error saving edited document: {e}")
else:
    print("\n❌ No chunks were processed. Output file not created.")