#!/usr/bin/env python3
"""
Claude API Markdown Formatter

This script reads a markdown file and uses Claude API to format it according to
a detailed prompt stored in a text file.
"""

import os
import sys
import json
import requests
from pathlib import Path
from typing import Optional


class ClaudeMarkdownFormatter:
    """
    Uses Claude API to format markdown documents based on a detailed prompt.
    """
    
    def __init__(self, api_key: str, model: str = "claude-3-5-sonnet-20241022"):
        """
        Initialize the Claude formatter.
        
        Args:
            api_key: Claude API key
            model: Claude model to use
        """
        self.api_key = api_key
        self.model = model
        self.base_url = "https://api.anthropic.com/v1/messages"
        self.headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
    
    def load_prompt(self, prompt_file: str) -> str:
        """
        Load the formatting prompt from a text file.
        
        Args:
            prompt_file: Path to the prompt file
            
        Returns:
            The prompt content as a string
        """
        try:
            with open(prompt_file, 'r', encoding='utf-8') as f:
                return f.read().strip()
        except FileNotFoundError:
            print(f"Error: Prompt file not found: {prompt_file}")
            return ""
        except Exception as e:
            print(f"Error reading prompt file: {e}")
            return ""
    
    def load_markdown(self, input_file: str) -> str:
        """
        Load the markdown content from file.
        
        Args:
            input_file: Path to the markdown file
            
        Returns:
            The markdown content as a string
        """
        try:
            with open(input_file, 'r', encoding='utf-8') as f:
                return f.read()
        except FileNotFoundError:
            print(f"Error: Input file not found: {input_file}")
            return ""
        except Exception as e:
            print(f"Error reading input file: {e}")
            return ""
    
    def format_with_claude(self, markdown_content: str, prompt: str) -> Optional[str]:
        """
        Send the markdown content to Claude API for formatting.
        
        Args:
            markdown_content: The markdown content to format
            prompt: The formatting prompt to use
            
        Returns:
            The formatted markdown content, or None if there was an error
        """
        try:
            payload = {
                "model": self.model,
                "max_tokens": 4000,
                "messages": [
                    {
                        "role": "user",
                        "content": f"{prompt}\n\nHere is the markdown content to format:\n\n{markdown_content}"
                    }
                ]
            }
            
            print("Sending request to Claude API...")
            response = requests.post(self.base_url, headers=self.headers, json=payload)
            
            if response.status_code == 200:
                result = response.json()
                formatted_content = result['content'][0]['text']
                print("✅ Claude API request successful")
                return formatted_content
            else:
                print(f"❌ Claude API error: {response.status_code}")
                print(f"Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"❌ Error calling Claude API: {e}")
            return None
    
    def format_document(self, input_file: str, output_file: str, prompt_file: str) -> bool:
        """
        Format a markdown document using Claude API.
        
        Args:
            input_file: Path to input markdown file
            output_file: Path to output formatted file
            prompt_file: Path to prompt file
            
        Returns:
            True if successful, False otherwise
        """
        print(f"📖 Loading markdown from: {input_file}")
        markdown_content = self.load_markdown(input_file)
        if not markdown_content:
            return False
        
        print(f"📝 Loading prompt from: {prompt_file}")
        prompt = self.load_prompt(prompt_file)
        if not prompt:
            return False
        
        print(f"🤖 Sending to Claude API for formatting...")
        formatted_content = self.format_with_claude(markdown_content, prompt)
        if not formatted_content:
            return False
        
        print(f"💾 Saving formatted content to: {output_file}")
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(formatted_content)
            print("✅ Formatting complete!")
            return True
        except Exception as e:
            print(f"❌ Error saving output file: {e}")
            return False


def main():
    """
    Main function to run the Claude markdown formatter.
    """
    # Check for API key
    api_key = os.getenv('CLAUDE_API_KEY')
    if not api_key:
        print("❌ Error: CLAUDE_API_KEY environment variable not set")
        print("Please set your Claude API key:")
        print("export CLAUDE_API_KEY='your_api_key_here'")
        return 1
    
    # Default file paths for our local environment
    input_file = "saved_markdowns/processed_document.md"
    output_file = "saved_markdowns/processed_document_claude_formatted.md"
    prompt_file = "formatting_prompt.txt"
    
    # Allow command line arguments to override defaults
    if len(sys.argv) > 1:
        input_file = sys.argv[1]
    if len(sys.argv) > 2:
        output_file = sys.argv[2]
    if len(sys.argv) > 3:
        prompt_file = sys.argv[3]
    
    print(f"🔧 Claude Markdown Formatter")
    print(f"📁 Input: {input_file}")
    print(f"📁 Output: {output_file}")
    print(f"📁 Prompt: {prompt_file}")
    print("=" * 50)
    
    # Initialize formatter
    formatter = ClaudeMarkdownFormatter(api_key)
    
    # Format the document
    success = formatter.format_document(input_file, output_file, prompt_file)
    
    if success:
        print("🎉 Formatting completed successfully!")
        return 0
    else:
        print("💥 Formatting failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())