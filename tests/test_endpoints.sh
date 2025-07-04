#!/bin/bash

# AmplifAI Execution Engine v1 - API Testing Script
# This script tests all the available endpoints with sample data

# Configuration
BASE_URL="http://localhost:8000"
CONTENT_TYPE="application/json"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    local status=$1
    local message=$2
    
    case $status in
        "INFO")
            echo -e "${BLUE}[INFO]${NC} $message"
            ;;
        "SUCCESS")
            echo -e "${GREEN}[SUCCESS]${NC} $message"
            ;;
        "ERROR")
            echo -e "${RED}[ERROR]${NC} $message"
            ;;
        "WARNING")
            echo -e "${YELLOW}[WARNING]${NC} $message"
            ;;
    esac
}

# Function to test endpoint
test_endpoint() {
    local method=$1
    local endpoint=$2
    local data=$3
    local expected_status=$4
    
    print_status "INFO" "Testing $method $endpoint"
    
    if [ -z "$data" ]; then
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint")
    else
        response=$(curl -s -w "\n%{http_code}" -X $method "$BASE_URL$endpoint" \
            -H "Content-Type: $CONTENT_TYPE" \
            -d "$data")
    fi
    
    # Extract status code (last line)
    status_code=$(echo "$response" | tail -n1)
    # Extract response body (all but last line)
    response_body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" -eq "$expected_status" ]; then
        print_status "SUCCESS" "✅ $method $endpoint - Status: $status_code"
        echo -e "${GREEN}Response:${NC} $response_body\n"
    else
        print_status "ERROR" "❌ $method $endpoint - Expected: $expected_status, Got: $status_code"
        echo -e "${RED}Response:${NC} $response_body\n"
    fi
}

# Function to check if server is running
check_server() {
    print_status "INFO" "Checking if server is running at $BASE_URL"
    
    if curl -s --connect-timeout 5 "$BASE_URL/status" > /dev/null 2>&1; then
        print_status "SUCCESS" "✅ Server is running"
        return 0
    else
        print_status "ERROR" "❌ Server is not running. Please start the server first:"
        echo "   uvicorn main:app --reload --host 0.0.0.0 --port 8000"
        return 1
    fi
}

# Main testing function
run_tests() {
    echo "================================================"
    echo "AmplifAI Execution Engine v1 - API Testing"
    echo "================================================"
    
    # Check if server is running
    if ! check_server; then
        exit 1
    fi
    
    echo ""
    
    # Test 1: Root endpoint
    test_endpoint "GET" "/" "" 200
    
    # Test 2: Status endpoint
    test_endpoint "GET" "/status" "" 200
    
    # Test 3: Launch Campaign endpoint
    campaign_data=$(cat tests/launch_campaign.json)
    test_endpoint "POST" "/launch-campaign" "$campaign_data" 200
    
    # Test 4: Upload Playbook endpoint
    playbook_data=$(cat tests/upload_playbook.json)
    test_endpoint "POST" "/upload-playbook" "$playbook_data" 200
    
    # Test 5: Generic Route endpoint
    route_data='{
        "payload": {
            "action": "process_analytics",
            "data": {
                "metric": "engagement_rate",
                "value": 3.5,
                "timestamp": "2024-01-01T12:00:00Z"
            }
        },
        "metadata": {
            "source": "external_api",
            "priority": "high",
            "session_id": "test_session_001"
        }
    }'
    test_endpoint "POST" "/route/analytics" "$route_data" 200
    
    # Test 6: Another generic route
    route_data2='{
        "payload": {
            "action": "send_notification",
            "recipient": "user@example.com",
            "message": "Your campaign is performing well!"
        },
        "metadata": {
            "source": "automation",
            "priority": "medium"
        }
    }'
    test_endpoint "POST" "/route/notifications" "$route_data2" 200
    
    # Test 7: Logs Stats endpoint
    test_endpoint "GET" "/logs/stats" "" 200
    
    # Test 8: Memory Stats endpoint
    test_endpoint "GET" "/memory/stats" "" 200
    
    # Test 9: Invalid endpoint (should return 404)
    test_endpoint "GET" "/invalid-endpoint" "" 404
    
    # Test 10: Invalid campaign data (should return 422)
    invalid_campaign_data='{
        "campaign_id": "",
        "budget": -100,
        "audience": [],
        "creatives": []
    }'
    test_endpoint "POST" "/launch-campaign" "$invalid_campaign_data" 422
    
    echo "================================================"
    echo "Testing completed!"
    echo "================================================"
}

# Additional test functions
test_concurrent_requests() {
    echo ""
    print_status "INFO" "Testing concurrent requests..."
    
    # Launch 5 concurrent campaign requests
    for i in {1..5}; do
        campaign_data=$(cat tests/launch_campaign.json | sed "s/camp_social_media_2024_001/camp_concurrent_$i/g")
        curl -s -X POST "$BASE_URL/launch-campaign" \
            -H "Content-Type: $CONTENT_TYPE" \
            -d "$campaign_data" > /dev/null &
    done
    
    wait
    print_status "SUCCESS" "✅ Concurrent requests completed"
}

test_file_upload() {
    echo ""
    print_status "INFO" "Testing file upload endpoint..."
    
    # Create a temporary JSON file for testing
    cat > /tmp/test_playbook.json << 'EOF'
{
    "name": "Test Playbook from File",
    "steps": [
        {"action": "step1", "description": "First step"},
        {"action": "step2", "description": "Second step"}
    ]
}
EOF
    
    # Test file upload
    response=$(curl -s -w "\n%{http_code}" -X POST "$BASE_URL/upload-playbook-file" \
        -F "file=@/tmp/test_playbook.json" \
        -F "playbook_name=Test File Upload" \
        -F "version=1.0" \
        -F "tags=test,file,upload")
    
    status_code=$(echo "$response" | tail -n1)
    response_body=$(echo "$response" | head -n -1)
    
    if [ "$status_code" -eq 200 ]; then
        print_status "SUCCESS" "✅ File upload test passed"
        echo -e "${GREEN}Response:${NC} $response_body"
    else
        print_status "ERROR" "❌ File upload test failed - Status: $status_code"
        echo -e "${RED}Response:${NC} $response_body"
    fi
    
    # Clean up
    rm -f /tmp/test_playbook.json
}

# Performance testing
performance_test() {
    echo ""
    print_status "INFO" "Running performance test..."
    
    # Test response time for status endpoint
    start_time=$(date +%s%N)
    curl -s "$BASE_URL/status" > /dev/null
    end_time=$(date +%s%N)
    
    duration=$((($end_time - $start_time) / 1000000))
    
    if [ "$duration" -lt 1000 ]; then
        print_status "SUCCESS" "✅ Response time: ${duration}ms (Good)"
    elif [ "$duration" -lt 5000 ]; then
        print_status "WARNING" "⚠️  Response time: ${duration}ms (Acceptable)"
    else
        print_status "ERROR" "❌ Response time: ${duration}ms (Poor)"
    fi
}

# Help function
show_help() {
    echo "AmplifAI Execution Engine v1 - API Testing Script"
    echo ""
    echo "Usage: $0 [OPTIONS]"
    echo ""
    echo "Options:"
    echo "  -h, --help          Show this help message"
    echo "  -a, --all           Run all tests (default)"
    echo "  -b, --basic         Run basic endpoint tests only"
    echo "  -c, --concurrent    Run concurrent request tests"
    echo "  -f, --file          Test file upload endpoint"
    echo "  -p, --performance   Run performance tests"
    echo "  -u, --url URL       Set base URL (default: http://localhost:8000)"
    echo ""
    echo "Examples:"
    echo "  $0                  # Run all tests"
    echo "  $0 --basic          # Run basic tests only"
    echo "  $0 --url http://localhost:3000  # Test against different port"
    echo ""
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_help
            exit 0
            ;;
        -a|--all)
            RUN_ALL=true
            shift
            ;;
        -b|--basic)
            RUN_BASIC=true
            shift
            ;;
        -c|--concurrent)
            RUN_CONCURRENT=true
            shift
            ;;
        -f|--file)
            RUN_FILE=true
            shift
            ;;
        -p|--performance)
            RUN_PERFORMANCE=true
            shift
            ;;
        -u|--url)
            BASE_URL="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Default to run all tests if no specific option is provided
if [ -z "$RUN_BASIC" ] && [ -z "$RUN_CONCURRENT" ] && [ -z "$RUN_FILE" ] && [ -z "$RUN_PERFORMANCE" ]; then
    RUN_ALL=true
fi

# Run selected tests
if [ "$RUN_ALL" = true ] || [ "$RUN_BASIC" = true ]; then
    run_tests
fi

if [ "$RUN_ALL" = true ] || [ "$RUN_CONCURRENT" = true ]; then
    test_concurrent_requests
fi

if [ "$RUN_ALL" = true ] || [ "$RUN_FILE" = true ]; then
    test_file_upload
fi

if [ "$RUN_ALL" = true ] || [ "$RUN_PERFORMANCE" = true ]; then
    performance_test
fi

echo ""
print_status "INFO" "All tests completed!"
print_status "INFO" "Check the logs and memory directories for generated data" 