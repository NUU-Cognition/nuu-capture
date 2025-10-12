"""MinerU API client for document parsing."""

import os
import time
import base64
import zipfile
import requests
from typing import Dict, Optional, Tuple, Any
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()


class MinerUClient:
    """Client for interacting with the MinerU API."""

    BASE_URL: str = "https://mineru.net/api/v4"

    def __init__(self, api_key: Optional[str] = None) -> None:
        """
        Initialize the MinerU API client.

        Args:
            api_key: MinerU API key. If not provided, will read from MINER_U_API_KEY env var.
        """
        self.api_key: str = api_key or os.getenv("MINER_U_API_KEY", "")
        if not self.api_key:
            raise ValueError("MinerU API key not provided. Set MINER_U_API_KEY env var or pass api_key parameter.")

        self.headers: Dict[str, str] = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "*/*"
        }

    def upload_file_to_url(self, file_path: str, upload_url: str) -> None:
        """
        Upload a PDF file to a pre-signed URL.

        Args:
            file_path: Path to the PDF file to upload.
            upload_url: The pre-signed URL to upload to.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            requests.RequestException: If the upload fails.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        print(f"Uploading file...")
        with open(file_path, 'rb') as f:
            file_content: bytes = f.read()

        # Don't add extra headers for signed OSS URLs - they will break the signature
        upload_response = requests.put(
            upload_url,
            data=file_content
        )
        upload_response.raise_for_status()

        print(f"File uploaded successfully!")

    def upload_file(self, file_path: str) -> str:
        """
        Upload a PDF file using batch upload and get the OSS URL.

        Args:
            file_path: Path to the PDF file to upload.

        Returns:
            The OSS URL where the file was uploaded.

        Raises:
            FileNotFoundError: If the file doesn't exist.
            requests.RequestException: If the upload fails.
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Step 1: Request upload URL via batch endpoint
        batch_url: str = f"{self.BASE_URL}/file-urls/batch"
        filename: str = Path(file_path).name

        batch_payload: Dict[str, Any] = {
            "files": [{"name": filename}]
        }

        print(f"Requesting upload URL for {filename}...")
        batch_response = requests.post(
            batch_url,
            headers={**self.headers, "Content-Type": "application/json"},
            json=batch_payload
        )
        batch_response.raise_for_status()
        batch_data: Dict[str, Any] = batch_response.json()

        if batch_data.get("code") != 0:
            raise ValueError(f"API error: {batch_data.get('msg', 'Unknown error')}")

        data: Dict[str, Any] = batch_data.get("data", {})
        file_urls: list[str] = data.get("file_urls", [])

        if not file_urls or len(file_urls) == 0:
            raise ValueError("Failed to get upload URL from batch endpoint")

        upload_url: str = file_urls[0]

        # Step 2: Upload the file to the provided URL
        self.upload_file_to_url(file_path, upload_url)

        # Return the base OSS URL (without query parameters) for task submission
        # The uploaded file is accessible at the signed URL but we need to use
        # a public URL for task submission
        # Extract the base URL before the '?' for query parameters
        base_url: str = upload_url.split('?')[0]

        print(f"File available at: {base_url}")
        return base_url

    def submit_parsing_task(
        self,
        file_url: str,
        is_ocr: bool = True,
        enable_formula: bool = True
    ) -> str:
        """
        Submit a parsing task for a previously uploaded file.

        Args:
            file_url: The URL of the uploaded file.
            is_ocr: Whether to enable OCR for scanned documents.
            enable_formula: Whether to enable formula recognition.

        Returns:
            The task ID for polling.

        Raises:
            requests.RequestException: If the task submission fails.
        """
        task_url: str = f"{self.BASE_URL}/extract/task"

        task_payload: Dict[str, Any] = {
            "url": file_url,
            "is_ocr": is_ocr,
            "enable_formula": enable_formula
        }

        headers_with_json: Dict[str, str] = {
            **self.headers,
            "Content-Type": "application/json"
        }

        print(f"Submitting parsing task...")
        task_response = requests.post(
            task_url,
            headers=headers_with_json,
            json=task_payload
        )
        task_response.raise_for_status()
        task_data: Dict[str, Any] = task_response.json()

        print(f"Task response: {task_data}")

        if task_data.get("code") != 0:
            raise ValueError(f"Task submission error: {task_data.get('msg', 'Unknown error')}")

        data: Dict[str, Any] = task_data.get("data", {})
        task_id: str = data.get("task_id", "")

        if not task_id:
            raise ValueError(f"Failed to get task ID from response: {task_data}")

        print(f"Task submitted with ID: {task_id}")
        return task_id

    def get_task_status(self, task_id: str) -> Dict[str, Any]:
        """
        Get the status of a parsing task.

        Args:
            task_id: The task ID to check.

        Returns:
            Dictionary containing task status information.

        Raises:
            requests.RequestException: If the status check fails.
        """
        status_url: str = f"{self.BASE_URL}/extract/task/{task_id}"

        status_response = requests.get(
            status_url,
            headers=self.headers
        )
        status_response.raise_for_status()
        return status_response.json()

    def wait_for_completion(
        self,
        task_id: str,
        poll_interval: int = 5,
        max_wait_time: int = 600
    ) -> Dict[str, Any]:
        """
        Wait for a parsing task to complete.

        Args:
            task_id: The task ID to wait for.
            poll_interval: Seconds to wait between status checks.
            max_wait_time: Maximum seconds to wait before timing out.

        Returns:
            The final task status data.

        Raises:
            TimeoutError: If the task doesn't complete within max_wait_time.
            ValueError: If the task fails.
        """
        start_time: float = time.time()

        print(f"Waiting for task {task_id} to complete...")

        while True:
            if time.time() - start_time > max_wait_time:
                raise TimeoutError(f"Task {task_id} did not complete within {max_wait_time} seconds")

            status_data: Dict[str, Any] = self.get_task_status(task_id)

            if not status_data.get("data"):
                raise ValueError("Invalid status response from API")

            task_status: str = status_data["data"].get("status", "")

            print(f"Task status: {task_status}")

            if task_status == "completed":
                print("Task completed successfully!")
                return status_data
            elif task_status == "failed":
                error_msg: str = status_data["data"].get("error", "Unknown error")
                raise ValueError(f"Task failed: {error_msg}")
            elif task_status in ["pending", "processing"]:
                time.sleep(poll_interval)
            else:
                print(f"Unknown status: {task_status}, continuing to wait...")
                time.sleep(poll_interval)

    def download_results(self, task_data: Dict[str, Any], output_dir: str) -> Tuple[str, str]:
        """
        Download markdown and JSON results from a completed task.

        Args:
            task_data: The task status data containing result URLs.
            output_dir: Directory to save the results.

        Returns:
            Tuple of (markdown_path, json_path).

        Raises:
            ValueError: If result URLs are not available.
            requests.RequestException: If download fails.
        """
        os.makedirs(output_dir, exist_ok=True)

        data: Dict[str, Any] = task_data.get("data", {})
        markdown_url: Optional[str] = data.get("md_url")
        json_url: Optional[str] = data.get("json_url")

        if not markdown_url or not json_url:
            raise ValueError("Result URLs not available in task data")

        # Download markdown
        print(f"Downloading markdown from {markdown_url}...")
        md_response = requests.get(markdown_url)
        md_response.raise_for_status()

        markdown_path: str = os.path.join(output_dir, "document.md")
        with open(markdown_path, 'wb') as f:
            f.write(md_response.content)
        print(f"Markdown saved to: {markdown_path}")

        # Download JSON
        print(f"Downloading JSON from {json_url}...")
        json_response = requests.get(json_url)
        json_response.raise_for_status()

        json_path: str = os.path.join(output_dir, "document.json")
        with open(json_path, 'wb') as f:
            f.write(json_response.content)
        print(f"JSON saved to: {json_path}")

        return markdown_path, json_path

    def download_and_extract_zip(self, zip_url: str, output_dir: str) -> Tuple[str, str]:
        """
        Download and extract ZIP file containing markdown and JSON results.

        Args:
            zip_url: URL of the ZIP file to download.
            output_dir: Directory to extract the results to.

        Returns:
            Tuple of (markdown_path, json_path).

        Raises:
            requests.RequestException: If download fails.
            ValueError: If required files are not found in ZIP.
        """
        os.makedirs(output_dir, exist_ok=True)

        # Download ZIP file
        print(f"Downloading results from {zip_url}...")
        zip_response = requests.get(zip_url)
        zip_response.raise_for_status()

        # Save ZIP temporarily
        zip_path: str = os.path.join(output_dir, "results.zip")
        with open(zip_path, 'wb') as f:
            f.write(zip_response.content)

        print(f"Extracting results...")

        # Extract ZIP
        with zipfile.ZipFile(zip_path, 'r') as zip_ref:
            zip_ref.extractall(output_dir)

        # Find markdown and JSON files
        markdown_path: Optional[str] = None
        json_path: Optional[str] = None

        for root, dirs, files in os.walk(output_dir):
            for file in files:
                if file.endswith('.md') and 'auto' in file.lower():
                    markdown_path = os.path.join(root, file)
                elif file.endswith('.json') and 'content_list' in file.lower():
                    json_path = os.path.join(root, file)

        # If not found with specific names, look for any .md and .json
        if not markdown_path or not json_path:
            for root, dirs, files in os.walk(output_dir):
                for file in files:
                    if not markdown_path and file.endswith('.md'):
                        markdown_path = os.path.join(root, file)
                    if not json_path and file.endswith('.json'):
                        json_path = os.path.join(root, file)

        if not markdown_path:
            raise ValueError("Markdown file not found in extracted results")
        if not json_path:
            raise ValueError("JSON file not found in extracted results")

        # Rename to standard names
        final_md_path: str = os.path.join(output_dir, "document.md")
        final_json_path: str = os.path.join(output_dir, "document.json")

        if markdown_path != final_md_path:
            os.rename(markdown_path, final_md_path)
        if json_path != final_json_path:
            os.rename(json_path, final_json_path)

        # Clean up ZIP file
        try:
            os.remove(zip_path)
        except:
            pass

        print(f"Results extracted successfully!")
        print(f"Markdown: {final_md_path}")
        print(f"JSON: {final_json_path}")

        return final_md_path, final_json_path

    def parse_document_batch(
        self,
        file_path: str,
        output_dir: str
    ) -> Tuple[str, str]:
        """
        Complete end-to-end document parsing workflow using batch upload.

        When using the batch upload endpoint, the system automatically
        submits parsing tasks after successful upload.

        Args:
            file_path: Path to the PDF file to parse.
            output_dir: Directory to save the results.

        Returns:
            Tuple of (markdown_path, json_path).
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File not found: {file_path}")

        # Get batch upload URL
        batch_url: str = f"{self.BASE_URL}/file-urls/batch"
        filename: str = Path(file_path).name

        batch_payload: Dict[str, Any] = {
            "files": [{"name": filename}]
        }

        print(f"Requesting upload URL for {filename}...")
        batch_response = requests.post(
            batch_url,
            headers={**self.headers, "Content-Type": "application/json"},
            json=batch_payload
        )
        batch_response.raise_for_status()
        batch_data: Dict[str, Any] = batch_response.json()

        if batch_data.get("code") != 0:
            raise ValueError(f"API error: {batch_data.get('msg', 'Unknown error')}")

        data: Dict[str, Any] = batch_data.get("data", {})
        file_urls: list[str] = data.get("file_urls", [])
        batch_id: str = data.get("batch_id", "")

        if not file_urls or len(file_urls) == 0:
            raise ValueError("Failed to get upload URL from batch endpoint")

        upload_url: str = file_urls[0]

        # Upload the file
        print(f"Uploading file...")
        with open(file_path, 'rb') as f:
            file_content: bytes = f.read()

        # Don't add extra headers for signed OSS URLs - they will break the signature
        upload_response = requests.put(
            upload_url,
            data=file_content
        )
        upload_response.raise_for_status()

        print(f"File uploaded successfully! Batch ID: {batch_id}")
        print("Waiting for automatic task creation...")

        # Wait for automatic task creation
        time.sleep(10)

        # List tasks to find the one for this batch
        list_tasks_url: str = f"{self.BASE_URL}/extract/tasks"

        # Get recent tasks
        list_response = requests.get(
            list_tasks_url,
            headers=self.headers,
            params={"page": 1, "page_size": 10}
        )
        list_response.raise_for_status()
        list_data: Dict[str, Any] = list_response.json()

        if list_data.get("code") != 0:
            raise ValueError(f"Failed to list tasks: {list_data.get('msg', 'Unknown error')}")

        tasks_list: list[Dict[str, Any]] = list_data.get("data", {}).get("list", [])

        # Find the most recent task (should be ours)
        if not tasks_list or len(tasks_list) == 0:
            raise ValueError("No tasks found after upload. Task creation may have failed.")

        task_id: str = tasks_list[0].get("task_id", "")
        if not task_id:
            raise ValueError("Invalid task ID from task list")

        print(f"Found task ID: {task_id}")

        # Poll task status until complete
        max_retries: int = 120  # 10 minutes with 5 second intervals
        for i in range(max_retries):
            print(f"Checking task status (attempt {i+1}/{max_retries})...")

            task_status_data: Dict[str, Any] = self.get_task_status(task_id)

            if task_status_data.get("code") != 0:
                raise ValueError(f"Task status error: {task_status_data.get('msg', 'Unknown error')}")

            task_info: Dict[str, Any] = task_status_data.get("data", {})
            state: str = task_info.get("state", "")

            print(f"Task state: {state}")

            if state == "done":
                print("Task completed successfully!")

                # Get the full ZIP URL
                zip_url: Optional[str] = task_info.get("full_zip_url")
                if not zip_url:
                    raise ValueError("No results URL in completed task")

                # Download and extract ZIP
                return self.download_and_extract_zip(zip_url, output_dir)

            elif state == "failed":
                error_msg: str = task_info.get("err_msg", "Unknown error")
                raise ValueError(f"Task failed: {error_msg}")

            elif state == "running":
                # Show progress if available
                progress: Dict[str, Any] = task_info.get("extract_progress", {})
                if progress:
                    extracted: int = progress.get("extracted_pages", 0)
                    total: int = progress.get("total_pages", 0)
                    print(f"  Progress: {extracted}/{total} pages extracted")

            time.sleep(5)

        raise TimeoutError("Task did not complete within expected time")

    def parse_document(
        self,
        file_path: str,
        output_dir: str,
        is_ocr: bool = True,
        enable_formula: bool = True
    ) -> Tuple[str, str]:
        """
        Complete end-to-end document parsing workflow.

        Args:
            file_path: Path to the PDF file to parse.
            output_dir: Directory to save the results.
            is_ocr: Whether to enable OCR for scanned documents.
            enable_formula: Whether to enable formula recognition.

        Returns:
            Tuple of (markdown_path, json_path).
        """
        # Upload file and get the URL
        file_url: str = self.upload_file(file_path)

        # Submit parsing task with the file URL
        task_id: str = self.submit_parsing_task(file_url, is_ocr, enable_formula)

        # Poll task status until complete
        max_retries: int = 120  # 10 minutes with 5 second intervals
        for i in range(max_retries):
            print(f"Checking task status (attempt {i+1}/{max_retries})...")

            task_status_data: Dict[str, Any] = self.get_task_status(task_id)

            if task_status_data.get("code") != 0:
                raise ValueError(f"Task status error: {task_status_data.get('msg', 'Unknown error')}")

            task_info: Dict[str, Any] = task_status_data.get("data", {})
            state: str = task_info.get("state", "")

            print(f"Task state: {state}")

            if state == "done":
                print("Task completed successfully!")

                # Get the full ZIP URL
                zip_url: Optional[str] = task_info.get("full_zip_url")
                if not zip_url:
                    raise ValueError("No results URL in completed task")

                # Download and extract ZIP
                return self.download_and_extract_zip(zip_url, output_dir)

            elif state == "failed":
                error_msg: str = task_info.get("err_msg", "Unknown error")
                raise ValueError(f"Task failed: {error_msg}")

            elif state == "running":
                # Show progress if available
                progress: Dict[str, Any] = task_info.get("extract_progress", {})
                if progress:
                    extracted: int = progress.get("extracted_pages", 0)
                    total: int = progress.get("total_pages", 0)
                    print(f"  Progress: {extracted}/{total} pages extracted")

            time.sleep(5)

        raise TimeoutError("Task did not complete within expected time")
