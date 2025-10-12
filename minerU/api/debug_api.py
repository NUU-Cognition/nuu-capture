"""Debug script to test MinerU API responses."""

import os
import requests
import json
from dotenv import load_dotenv

load_dotenv()

api_key = os.getenv("MINER_U_API_KEY")
if not api_key:
    print("Error: MINER_U_API_KEY not found in environment")
    exit(1)

headers = {
    "Authorization": f"Bearer {api_key}",
    "Accept": "*/*",
    "Content-Type": "application/json"
}

# Test 1: Request batch upload URL
print("=" * 60)
print("Test 1: Request batch upload URL")
print("=" * 60)

batch_url = "https://mineru.net/api/v4/file-urls/batch"
batch_payload = {
    "files": [{"name": "doc.pdf"}]
}

print(f"URL: {batch_url}")
print(f"Headers: {json.dumps({k: v[:20] + '...' if k == 'Authorization' else v for k, v in headers.items()}, indent=2)}")
print(f"Payload: {json.dumps(batch_payload, indent=2)}")
print()

try:
    response = requests.post(batch_url, headers=headers, json=batch_payload)
    print(f"Status Code: {response.status_code}")
    print(f"Response Headers: {dict(response.headers)}")
    print(f"Response Body:")
    try:
        print(json.dumps(response.json(), indent=2))
    except:
        print(response.text)
except Exception as e:
    print(f"Error: {e}")

print()
print("=" * 60)
