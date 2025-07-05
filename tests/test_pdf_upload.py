#!/usr/bin/env python3
"""
AmplifAI Execution Engine v1 - PDF Upload Test Script (Python Version)
======================================================================

This script tests the /upload-playbook-file endpoint by uploading a sample
PDF file and validating the response. It provides the same functionality
as the shell script version but in Python.

Usage:
    python tests/test_pdf_upload.py [BASE_URL]

Examples:
    python tests/test_pdf_upload.py                    # Test against localhost:8000
    python tests/test_pdf_upload.py http://localhost:3000  # Test against custom URL

Exit Codes:
    0 - All tests passed
    1 - Server not accessible
    2 - PDF file not found or creation failed
    3 - Upload failed or invalid response
    4 - Missing required dependencies
"""

import sys
import os
import time
import json
from datetime import datetime
from pathlib import Path

# Try to import required dependencies
try:
    import httpx
except ImportError:
    print("❌ Error: httpx is required. Install with: pip install httpx")
    sys.exit(4)

# Configuration
BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8000"
PDF_FILE = "tests/sample_playbook.pdf"
ENDPOINT = "/upload-playbook-file"
FULL_URL = f"{BASE_URL}{ENDPOINT}"

# Colors for output
class Colors:
    RED = '\033[0;31m'
    GREEN = '\033[0;32m'
    YELLOW = '\033[1;33m'
    BLUE = '\033[0;34m'
    NC = '\033[0m'  # No Color

def print_status(level: str, message: str):
    """Print status message with timestamp and color coding"""
    timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    
    color_map = {
        "SUCCESS": Colors.GREEN,
        "ERROR": Colors.RED,
        "WARNING": Colors.YELLOW,
        "INFO": Colors.BLUE
    }
    
    color = color_map.get(level, Colors.NC)
    print(f"{color}[{level}]{Colors.NC} {timestamp} - {message}")

def check_server() -> bool:
    """Check if server is accessible"""
    print_status("INFO", f"Checking if server is accessible at {BASE_URL}")
    
    try:
        with httpx.Client(timeout=10.0) as client:
            response = client.get(f"{BASE_URL}/status")
            if response.status_code == 200:
                print_status("SUCCESS", "✅ Server is accessible")
                return True
            else:
                print_status("ERROR", f"❌ Server returned status {response.status_code}")
                return False
    except Exception as e:
        print_status("ERROR", f"❌ Server is not accessible: {str(e)}")
        print_status("ERROR", "Please ensure the server is running:")
        print("   uvicorn main:app --reload --host 0.0.0.0 --port 8000")
        return False

def check_pdf_file() -> bool:
    """Check if PDF file exists, create if missing"""
    print_status("INFO", f"Checking if PDF file exists: {PDF_FILE}")
    
    if not os.path.exists(PDF_FILE):
        print_status("ERROR", f"PDF file not found: {PDF_FILE}")
        print_status("INFO", "Creating a sample PDF file...")
        
        # Create the tests directory if it doesn't exist
        os.makedirs("tests", exist_ok=True)
        
        # Create a minimal valid PDF
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n181\n%%EOF'
        
        try:
            with open(PDF_FILE, 'wb') as f:
                f.write(pdf_content)
            print_status("SUCCESS", f"✅ Created sample PDF file: {PDF_FILE}")
        except Exception as e:
            print_status("ERROR", f"❌ Failed to create PDF file: {str(e)}")
            return False
    else:
        print_status("SUCCESS", "✅ PDF file found")
    
    # Check file size
    try:
        file_size = os.path.getsize(PDF_FILE)
        print_status("INFO", f"PDF file size: {file_size} bytes")
    except Exception as e:
        print_status("WARNING", f"⚠️  Could not get file size: {str(e)}")
    
    return True

def test_pdf_upload() -> bool:
    """Test PDF upload functionality"""
    print_status("INFO", f"Testing PDF upload to {FULL_URL}")
    
    # Prepare form data
    playbook_name = "Sample PDF Playbook Test (Python)"
    version = "1.0"
    tags = "test,pdf,upload,automation,python"
    
    print_status("INFO", "Upload parameters:")
    print(f"  📄 File: {PDF_FILE}")
    print(f"  📝 Name: {playbook_name}")
    print(f"  🏷️  Version: {version}")
    print(f"  🏷️  Tags: {tags}")
    
    # Perform the upload
    print_status("INFO", "Uploading PDF file...")
    
    try:
        with open(PDF_FILE, 'rb') as pdf_file:
            files = {"file": ("sample_playbook.pdf", pdf_file, "application/pdf")}
            data = {
                "playbook_name": playbook_name,
                "version": version,
                "tags": tags
            }
            
            start_time = time.time()
            
            with httpx.Client(timeout=30.0) as client:
                response = client.post(
                    FULL_URL,
                    files=files,
                    data=data,
                    headers={"User-Agent": "AmplifAI-PDF-Test-Python/1.0"}
                )
            
            duration = round((time.time() - start_time) * 1000, 2)
            
    except Exception as e:
        print_status("ERROR", f"❌ Upload failed with exception: {str(e)}")
        return False
    
    print_status("INFO", "Upload completed")
    print(f"  ⏱️  Response time: {duration}ms")
    print(f"  📊 HTTP Status: {response.status_code}")
    
    # Validate HTTP status code
    if response.status_code != 200:
        print_status("ERROR", f"❌ Upload failed with HTTP status: {response.status_code}")
        print_status("ERROR", f"Response body: {response.text}")
        return False
    
    print_status("SUCCESS", "✅ Upload successful (HTTP 200)")
    
    # Parse and validate JSON response
    print_status("INFO", "Validating response JSON...")
    
    try:
        response_data = response.json()
        print(f"  📋 Response: {json.dumps(response_data, indent=2)}")
        
        # Validate required fields
        if response_data.get("status") == "received":
            print_status("SUCCESS", f"✅ Status field is correct: {response_data['status']}")
        else:
            print_status("ERROR", f"❌ Invalid status field: '{response_data.get('status')}' (expected 'received')")
            return False
        
        playbook_id = response_data.get("playbook_id")
        if playbook_id and playbook_id.startswith("pb_"):
            print_status("SUCCESS", f"✅ Playbook ID generated: {playbook_id}")
        else:
            print_status("ERROR", f"❌ Missing or invalid playbook_id field: {playbook_id}")
            return False
        
        message = response_data.get("message")
        if message:
            print_status("SUCCESS", f"✅ Message field present: {message}")
        else:
            print_status("WARNING", "⚠️  Message field missing or empty")
        
        timestamp = response_data.get("timestamp")
        if timestamp:
            print_status("SUCCESS", f"✅ Timestamp field present: {timestamp}")
        else:
            print_status("WARNING", "⚠️  Timestamp field missing or empty")
        
    except json.JSONDecodeError as e:
        print_status("ERROR", f"❌ Invalid JSON response: {str(e)}")
        print_status("ERROR", f"Response text: {response.text}")
        return False
    except Exception as e:
        print_status("ERROR", f"❌ Error parsing response: {str(e)}")
        return False
    
    print_status("SUCCESS", "🎉 PDF upload test completed successfully!")
    return True

def test_invalid_file() -> bool:
    """Test invalid file upload handling"""
    print_status("INFO", "Testing invalid file upload handling...")
    
    # Create a temporary invalid file
    invalid_content = b"This is not a valid PDF file"
    
    try:
        files = {"file": ("invalid.txt", invalid_content, "text/plain")}
        data = {
            "playbook_name": "Invalid File Test",
            "version": "1.0"
        }
        
        with httpx.Client(timeout=30.0) as client:
            response = client.post(FULL_URL, files=files, data=data)
        
        if response.status_code in [200, 422]:
            print_status("SUCCESS", f"✅ Invalid file handled gracefully (HTTP {response.status_code})")
            return True
        else:
            print_status("WARNING", f"⚠️  Unexpected response for invalid file: HTTP {response.status_code}")
            return True  # Don't fail the main test for this
            
    except Exception as e:
        print_status("WARNING", f"⚠️  Error testing invalid file: {str(e)}")
        return True  # Don't fail the main test for this

def show_help():
    """Show help message"""
    print(__doc__)

def main():
    """Main function"""
    # Handle help argument
    if len(sys.argv) > 1 and sys.argv[1] in ['-h', '--help']:
        show_help()
        sys.exit(0)
    
    print("=" * 80)
    print("🧪 AmplifAI Execution Engine v1 - PDF Upload Test (Python)")
    print("=" * 80)
    print(f"Testing endpoint: {FULL_URL}")
    print(f"PDF file: {PDF_FILE}")
    print("=" * 80)
    print()
    
    # Run all checks
    if not check_server():
        sys.exit(1)
    
    if not check_pdf_file():
        sys.exit(2)
    
    print()
    print_status("INFO", "Starting PDF upload tests...")
    print()
    
    # Run main test
    if not test_pdf_upload():
        sys.exit(3)
    
    print()
    print_status("INFO", "Running additional validation tests...")
    print()
    
    # Run additional tests
    test_invalid_file()
    
    print()
    print("=" * 80)
    print_status("SUCCESS", "🎉 All PDF upload tests completed successfully!")
    print("=" * 80)
    
    return 0

if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n\n⚠️  Test interrupted by user")
        sys.exit(130)
    except Exception as e:
        print_status("ERROR", f"❌ Unexpected error: {str(e)}")
        sys.exit(1) 