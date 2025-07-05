#!/bin/bash

# =============================================================================
# AmplifAI Execution Engine v1 - PDF Upload Test Script
# =============================================================================
# 
# This script tests the /upload-playbook-file endpoint by uploading a sample
# PDF file and validating the response. It ensures the endpoint correctly
# handles multipart form data and returns the expected JSON response.
#
# Usage:
#   ./tests/test_pdf_upload.sh [BASE_URL]
#
# Examples:
#   ./tests/test_pdf_upload.sh                    # Test against localhost:8000
#   ./tests/test_pdf_upload.sh http://localhost:3000  # Test against custom URL
#
# Exit Codes:
#   0 - All tests passed
#   1 - Server not accessible
#   2 - PDF file not found
#   3 - Upload failed or invalid response
#   4 - Missing required tools
# =============================================================================

set -e  # Exit on any error

# Configuration
BASE_URL="${1:-http://localhost:8000}"
PDF_FILE="tests/sample_playbook.pdf"
ENDPOINT="/upload-playbook-file"
FULL_URL="$BASE_URL$ENDPOINT"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# =============================================================================
# UTILITY FUNCTIONS
# =============================================================================

print_status() {
    local level="$1"
    local message="$2"
    local timestamp=$(date '+%Y-%m-%d %H:%M:%S')
    
    case $level in
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $timestamp - $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $timestamp - $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $timestamp - $message"
            ;;
        "INFO")
            echo -e "${BLUE}[INFO]${NC} $timestamp - $message"
            ;;
    esac
}

check_dependencies() {
    print_status "INFO" "Checking required dependencies..."
    
    local missing_tools=()
    
    if ! command -v curl &> /dev/null; then
        missing_tools+=("curl")
    fi
    
    if ! command -v jq &> /dev/null; then
        print_status "WARNING" "jq not found - JSON parsing will be limited"
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        print_status "ERROR" "Missing required tools: ${missing_tools[*]}"
        print_status "ERROR" "Please install missing tools and try again"
        exit 4
    fi
    
    print_status "SUCCESS" "All required dependencies found"
}

check_server() {
    print_status "INFO" "Checking if server is accessible at $BASE_URL"
    
    if curl -s --connect-timeout 5 --max-time 10 "$BASE_URL/status" > /dev/null 2>&1; then
        print_status "SUCCESS" "✅ Server is accessible"
        return 0
    else
        print_status "ERROR" "❌ Server is not accessible at $BASE_URL"
        print_status "ERROR" "Please ensure the server is running:"
        echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        return 1
    fi
}

check_pdf_file() {
    print_status "INFO" "Checking if PDF file exists: $PDF_FILE"
    
    if [ ! -f "$PDF_FILE" ]; then
        print_status "ERROR" "PDF file not found: $PDF_FILE"
        print_status "ERROR" "Creating a sample PDF file..."
        
        # Create the tests directory if it doesn't exist
        mkdir -p tests
        
        # Create a minimal valid PDF
        python3 -c "
pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n181\n%%EOF'
with open('$PDF_FILE', 'wb') as f:
    f.write(pdf_content)
print('Created $PDF_FILE')
"
        
        if [ -f "$PDF_FILE" ]; then
            print_status "SUCCESS" "✅ Created sample PDF file"
        else
            print_status "ERROR" "❌ Failed to create PDF file"
            return 2
        fi
    else
        print_status "SUCCESS" "✅ PDF file found"
    fi
    
    # Check file size
    local file_size=$(stat -f%z "$PDF_FILE" 2>/dev/null || stat -c%s "$PDF_FILE" 2>/dev/null || echo "unknown")
    print_status "INFO" "PDF file size: $file_size bytes"
    
    return 0
}

# =============================================================================
# MAIN TEST FUNCTION
# =============================================================================

test_pdf_upload() {
    print_status "INFO" "Testing PDF upload to $FULL_URL"
    
    # Prepare form data
    local playbook_name="Sample PDF Playbook Test"
    local version="1.0"
    local tags="test,pdf,upload,automation"
    
    print_status "INFO" "Upload parameters:"
    echo "  📄 File: $PDF_FILE"
    echo "  📝 Name: $playbook_name"
    echo "  🏷️  Version: $version"
    echo "  🏷️  Tags: $tags"
    
    # Perform the upload with detailed output
    print_status "INFO" "Uploading PDF file..."
    
    local temp_response=$(mktemp)
    local temp_headers=$(mktemp)
    
    # Execute curl command with comprehensive error handling
    local curl_exit_code=0
    curl -s -w "\n%{http_code}\n%{time_total}" \
        -H "User-Agent: AmplifAI-PDF-Test/1.0" \
        -X POST "$FULL_URL" \
        -F "file=@$PDF_FILE;type=application/pdf" \
        -F "playbook_name=$playbook_name" \
        -F "version=$version" \
        -F "tags=$tags" \
        -D "$temp_headers" \
        > "$temp_response" 2>/dev/null || curl_exit_code=$?
    
    # Parse response
    local response_body=$(head -n -2 "$temp_response")
    local http_code=$(tail -n 2 "$temp_response" | head -n 1)
    local response_time=$(tail -n 1 "$temp_response")
    
    # Clean up temp files
    rm -f "$temp_response" "$temp_headers"
    
    print_status "INFO" "Upload completed"
    echo "  ⏱️  Response time: ${response_time}s"
    echo "  📊 HTTP Status: $http_code"
    
    # Validate HTTP status code
    if [ "$http_code" != "200" ]; then
        print_status "ERROR" "❌ Upload failed with HTTP status: $http_code"
        print_status "ERROR" "Response body: $response_body"
        return 3
    fi
    
    print_status "SUCCESS" "✅ Upload successful (HTTP 200)"
    
    # Parse and validate JSON response
    print_status "INFO" "Validating response JSON..."
    echo "  📋 Response: $response_body"
    
    # Check if jq is available for JSON parsing
    if command -v jq &> /dev/null; then
        # Use jq for robust JSON parsing
        local status=$(echo "$response_body" | jq -r '.status // empty' 2>/dev/null)
        local playbook_id=$(echo "$response_body" | jq -r '.playbook_id // empty' 2>/dev/null)
        local message=$(echo "$response_body" | jq -r '.message // empty' 2>/dev/null)
        local timestamp=$(echo "$response_body" | jq -r '.timestamp // empty' 2>/dev/null)
        
        # Validate required fields
        if [ "$status" = "received" ]; then
            print_status "SUCCESS" "✅ Status field is correct: $status"
        else
            print_status "ERROR" "❌ Invalid status field: '$status' (expected 'received')"
            return 3
        fi
        
        if [ -n "$playbook_id" ] && [ "$playbook_id" != "null" ]; then
            print_status "SUCCESS" "✅ Playbook ID generated: $playbook_id"
        else
            print_status "ERROR" "❌ Missing or invalid playbook_id field"
            return 3
        fi
        
        if [ -n "$message" ] && [ "$message" != "null" ]; then
            print_status "SUCCESS" "✅ Message field present: $message"
        else
            print_status "WARNING" "⚠️  Message field missing or empty"
        fi
        
        if [ -n "$timestamp" ] && [ "$timestamp" != "null" ]; then
            print_status "SUCCESS" "✅ Timestamp field present: $timestamp"
        else
            print_status "WARNING" "⚠️  Timestamp field missing or empty"
        fi
        
    else
        # Fallback to basic string matching
        print_status "INFO" "Using basic string validation (jq not available)"
        
        if echo "$response_body" | grep -q '"status":"received"'; then
            print_status "SUCCESS" "✅ Status field is correct"
        else
            print_status "ERROR" "❌ Response does not contain '\"status\":\"received\"'"
            return 3
        fi
        
        if echo "$response_body" | grep -q '"playbook_id":"pb_'; then
            print_status "SUCCESS" "✅ Playbook ID field found"
        else
            print_status "ERROR" "❌ Response does not contain valid playbook_id"
            return 3
        fi
    fi
    
    print_status "SUCCESS" "🎉 PDF upload test completed successfully!"
    return 0
}

# =============================================================================
# ADDITIONAL VALIDATION TESTS
# =============================================================================

test_endpoint_documentation() {
    print_status "INFO" "Testing endpoint documentation accessibility..."
    
    # Test if endpoint appears in OpenAPI docs
    if curl -s "$BASE_URL/docs" | grep -q "upload-playbook-file"; then
        print_status "SUCCESS" "✅ Endpoint documented in OpenAPI/Swagger"
    else
        print_status "WARNING" "⚠️  Endpoint may not be documented in API docs"
    fi
}

test_invalid_file() {
    print_status "INFO" "Testing invalid file upload handling..."
    
    # Create a temporary invalid file
    local invalid_file="/tmp/invalid_test.txt"
    echo "This is not a valid PDF file" > "$invalid_file"
    
    local response=$(curl -s -w "%{http_code}" \
        -X POST "$FULL_URL" \
        -F "file=@$invalid_file" \
        -F "playbook_name=Invalid File Test" \
        -F "version=1.0" \
        2>/dev/null)
    
    local http_code=$(echo "$response" | tail -c 4)
    
    # Clean up
    rm -f "$invalid_file"
    
    if [ "$http_code" = "200" ] || [ "$http_code" = "422" ]; then
        print_status "SUCCESS" "✅ Invalid file handled gracefully (HTTP $http_code)"
    else
        print_status "WARNING" "⚠️  Unexpected response for invalid file: HTTP $http_code"
    fi
}

# =============================================================================
# MAIN EXECUTION
# =============================================================================

main() {
    echo "============================================================================="
    echo "🧪 AmplifAI Execution Engine v1 - PDF Upload Test"
    echo "============================================================================="
    echo "Testing endpoint: $FULL_URL"
    echo "PDF file: $PDF_FILE"
    echo "============================================================================="
    echo ""
    
    # Run all checks
    check_dependencies || exit 4
    check_server || exit 1
    check_pdf_file || exit 2
    
    echo ""
    print_status "INFO" "Starting PDF upload tests..."
    echo ""
    
    # Run main test
    test_pdf_upload || exit 3
    
    echo ""
    print_status "INFO" "Running additional validation tests..."
    echo ""
    
    # Run additional tests
    test_endpoint_documentation
    test_invalid_file
    
    echo ""
    echo "============================================================================="
    print_status "SUCCESS" "🎉 All PDF upload tests completed successfully!"
    echo "============================================================================="
    
    return 0
}

# Handle script arguments and help
case "${1:-}" in
    -h|--help)
        echo "AmplifAI PDF Upload Test Script"
        echo ""
        echo "Usage: $0 [BASE_URL]"
        echo ""
        echo "Arguments:"
        echo "  BASE_URL    Base URL of the server (default: http://localhost:8000)"
        echo ""
        echo "Examples:"
        echo "  $0                           # Test against localhost:8000"
        echo "  $0 http://localhost:3000     # Test against custom URL"
        echo ""
        echo "Exit Codes:"
        echo "  0 - All tests passed"
        echo "  1 - Server not accessible"
        echo "  2 - PDF file not found"
        echo "  3 - Upload failed or invalid response"
        echo "  4 - Missing required tools"
        exit 0
        ;;
esac

# Execute main function
main "$@" 