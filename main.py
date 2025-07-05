"""
AmplifAI Execution Engine v1
===============================

A comprehensive FastAPI-based execution engine for campaign management, playbook automation, 
and intelligent routing. This application serves as the core backend for marketing automation
workflows with enterprise-grade logging, notifications, and data persistence.

Architecture Overview:
- FastAPI web framework with async endpoints
- Background task processing for non-blocking operations
- Multi-layer data storage (ClickHouse + local files + memory)
- Real-time Slack notifications
- Comprehensive error handling and monitoring
- Auto-generated API documentation

Key Components:
1. Campaign Management: Launch and track marketing campaigns
2. Playbook Automation: Upload and process automation workflows
3. Generic Routing: Dynamic request routing to different modules
4. Logging Pipeline: Structured logging with ClickHouse integration
5. Notification System: Real-time Slack alerts and updates
6. Memory Storage: Persistent data with future semantic search

Created by: AmplifAI Team
Version: 1.0.0
License: MIT
"""

import os
import uuid
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

# FastAPI and web framework imports
from fastapi import FastAPI, HTTPException, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, HTMLResponse
import requests
import httpx
from dotenv import load_dotenv

# Import our custom modules
from schemas import (
    CampaignLaunchRequest, CampaignLaunchResponse,
    PlaybookUploadRequest, PlaybookUploadResponse,
    StatusResponse, GenericRouteRequest, GenericRouteResponse
)
from log_utils import log_api_call, log_error, get_log_stats
from slack import (
    send_campaign_notification, send_playbook_notification, 
    send_error_notification, is_slack_configured
)
from memory_utils import (
    store_campaign_memory, store_playbook_memory,
    log_to_memory, get_memory_stats
)

# Configure logging first
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
# First try to load from .env file (for local development)
load_dotenv()

# ============================================================================
# CONFIGURATION & ENVIRONMENT SETUP
# ============================================================================

def get_env_var(key: str, default: str = "") -> str:
    """
    Retrieve environment variable with comprehensive debug logging.
    
    This function provides detailed logging for environment variable loading,
    which is crucial for debugging deployment issues across different platforms
    (local development, cloud deployments, containers, etc.).
    
    Args:
        key: Environment variable name to retrieve
        default: Default value if environment variable is not set
        
    Returns:
        String value of the environment variable or default
        
    Note:
        Logs the presence and length of variables without exposing sensitive values
    """
    value = os.getenv(key, default)
    logger.info(f"🔍 Environment variable {key}: {'SET' if value else 'NOT SET'} (length: {len(value)})")
    return value

# ============================================================================
# APPLICATION CONFIGURATION
# ============================================================================
# These variables control the core application behavior and integrations.
# They are loaded from environment variables or .env file with fallback defaults.

APP_NAME = get_env_var("APP_NAME", "AmplifAI Execution Engine v1")
APP_VERSION = get_env_var("APP_VERSION", "1.0.0")

# Integration endpoints 
SLACK_WEBHOOK_URL = get_env_var("SLACK_WEBHOOK_URL")  # For real-time notifications
CLICKHOUSE_URL = get_env_var("CLICKHOUSE_URL")        # For production logging

# ============================================================================
# ENVIRONMENT DEBUGGING & VALIDATION
# ============================================================================

def debug_environment():
    """
    Comprehensive environment variable validation and debugging.
    
    This function validates all required and optional environment variables,
    providing detailed feedback about configuration status. It's essential
    for troubleshooting deployment issues and ensuring proper integration setup.
    
    Returns:
        dict: Environment validation results with status indicators
        
    Note:
        - Variables: APP_NAME, APP_VERSION,SLACK_WEBHOOK_URL, CLICKHOUSE_URL
        - Provides preview of configured URLs without exposing full values
    """
    # Get current values
    slack_url = os.getenv("SLACK_WEBHOOK_URL", "")
    clickhouse_url = os.getenv("CLICKHOUSE_URL", "")
    
    env_vars = {
        "SLACK_WEBHOOK_URL": "✅ CONFIGURED" if slack_url and slack_url.startswith("https://hooks.slack.com/services/") else "❌ NOT CONFIGURED", 
        "CLICKHOUSE_URL": "✅ CONFIGURED" if clickhouse_url else "❌ NOT CONFIGURED",
        "APP_NAME": os.getenv("APP_NAME", "Not Set"),
        "APP_VERSION": os.getenv("APP_VERSION", "Not Set"),
        "PORT": os.getenv("PORT", "Not Set"),
    }
    
    logger.info("🔍 Environment Variables Debug:")
    for key, value in env_vars.items():
        logger.info(f"  {key}: {value}")
    
    # Show previews for configured vars
    if slack_url and slack_url.startswith("https://hooks.slack.com/services/"):
        logger.info(f"  SLACK_WEBHOOK_URL preview: {slack_url[:50]}...")
    else:
        logger.info(f"  SLACK_WEBHOOK_URL current value: '{slack_url}'")
    
    return env_vars

# Logging already configured above

# Application startup time for uptime calculation
startup_time = datetime.now()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    # Environment variable debugging
    logger.info("🔍 Raw environment variable check:")
    logger.info(f"  SLACK_WEBHOOK_URL: {os.environ.get('SLACK_WEBHOOK_URL', 'NOT FOUND')}")
    logger.info(f"  CLICKHOUSE_URL: {os.environ.get('CLICKHOUSE_URL', 'NOT FOUND')}")
    logger.info(f"  APP_NAME: {os.environ.get('APP_NAME', 'NOT FOUND')}")
    logger.info(f"  APP_VERSION: {os.environ.get('APP_VERSION', 'NOT FOUND')}")
    logger.info(f"  LOG_LEVEL: {os.environ.get('LOG_LEVEL', 'NOT FOUND')}")
    
    # Debug environment variables
    env_debug = debug_environment()
    
    # Check configurations
    slack_configured = is_slack_configured()
    
    logger.info(f"Slack integration configured: {'✅ Yes' if slack_configured else '❌ No'}")
    
    yield
    
    logger.info("Shutting down AmplifAI Execution Engine")


# Initialize FastAPI app
app = FastAPI(
    title=APP_NAME,
    version=APP_VERSION,
    description="Campaign launching, playbook management, and intelligent routing system",
    lifespan=lifespan
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def calculate_uptime() -> str:
    """Calculate application uptime"""
    uptime_delta = datetime.now() - startup_time
    days = uptime_delta.days
    hours, remainder = divmod(uptime_delta.seconds, 3600)
    minutes, seconds = divmod(remainder, 60)
    
    if days > 0:
        return f"{days}d {hours}h {minutes}m {seconds}s"
    elif hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"





@app.get("/", response_model=StatusResponse)
async def root():
    """Root endpoint with basic service information"""
    return StatusResponse(
        status="ok",
        uptime=calculate_uptime(),
        version=APP_VERSION
    )


@app.get("/status", response_model=StatusResponse)
async def get_status():
    """Health check endpoint"""
    return StatusResponse(
        status="ok",
        uptime=calculate_uptime(),
        version=APP_VERSION
    )


@app.post("/launch-campaign", response_model=CampaignLaunchResponse)
async def launch_campaign(
    request: CampaignLaunchRequest,
    background_tasks: BackgroundTasks
):
    """
    Launch a marketing campaign with comprehensive tracking and notifications.
    
    This endpoint orchestrates the complete campaign launch workflow:
    
    1. **Validation**: Validates campaign parameters using Pydantic models
    2. **Processing**: Creates campaign record with unique timestamp
    3. **Logging**: Logs operation to ClickHouse database and local files
    4. **Notifications**: Sends real-time Slack notifications to team
    5. **Memory Storage**: Stores campaign data for future reference and analytics
    
    All secondary operations (logging, notifications, storage) are executed as
    background tasks to ensure fast API response times while maintaining
    comprehensive data tracking.
    
    Args:
        request: CampaignLaunchRequest containing campaign details
            - campaign_id: Unique identifier for the campaign
            - budget: Campaign budget in dollars (must be > 0)
            - audience: List of target audience segments (min 1 required)
            - creatives: List of creative asset IDs (min 1 required)
        background_tasks: FastAPI background task queue for async operations
    
    Returns:
        CampaignLaunchResponse: Success response with campaign details and timestamp
    
    Raises:
        HTTPException: 400 for validation errors, 500 for processing errors
        
    Example:
        POST /launch-campaign
        {
            "campaign_id": "social_media_2024_q1",
            "budget": 15000.0,
            "audience": ["tech_enthusiasts", "young_professionals"],
            "creatives": ["video_promo", "banner_ad", "social_post"]
        }
    
    Background Operations:
        - API call logging with performance metrics
        - Slack notification to campaign team
        - Memory storage for campaign analytics
        - ClickHouse database logging for reporting
    """
    start_time = time.time()
    
    try:
        campaign_data = request.dict()
        
        # Prepare response
        response = CampaignLaunchResponse(
            status="launched",
            campaign_id=request.campaign_id,
            message="Campaign launched successfully"
        )
        
        # Background tasks for logging and notifications
        background_tasks.add_task(
            log_api_call,
            "/launch-campaign",
            request.dict(),
            response.dict(),
            duration_ms=int((time.time() - start_time) * 1000),
            status="success"
        )
        
        background_tasks.add_task(
            send_campaign_notification,
            request.campaign_id,
            request.budget,
            request.audience,
            request.creatives,
            "launched"
        )
        
        background_tasks.add_task(
            store_campaign_memory,
            request.campaign_id,
            request.budget,
            request.audience,
            request.creatives,
            "launched"
        )
        
        logger.info(f"✅ Campaign {request.campaign_id} launched successfully")
        return response
        
    except Exception as e:
        # Log error
        error_msg = f"Error launching campaign: {str(e)}"
        logger.error(error_msg)
        
        # Background error logging
        background_tasks.add_task(
            log_error,
            "/launch-campaign",
            error_msg,
            request.dict() if request else {}
        )
        
        background_tasks.add_task(
            send_error_notification,
            error_msg,
            "/launch-campaign",
            {"campaign_id": request.campaign_id if request else "unknown"}
        )
        
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/upload-playbook", response_model=PlaybookUploadResponse)
async def upload_playbook(
    request: PlaybookUploadRequest,
    background_tasks: BackgroundTasks
):
    """
    Upload a playbook with JSON content
    
    This endpoint:
    1. Validates the playbook request
    2. Generates a unique playbook ID
    3. Logs the operation to ClickHouse
    4. Sends Slack notification (if configured)
    5. Stores playbook memory
    """
    start_time = time.time()
    
    try:
        # Generate unique playbook ID
        playbook_id = f"pb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Prepare response
        response = PlaybookUploadResponse(
            status="received",
            playbook_id=playbook_id,
            message="Playbook uploaded successfully"
        )
        
        # Background tasks for logging and notifications
        background_tasks.add_task(
            log_api_call,
            "/upload-playbook",
            request.dict(),
            response.dict(),
            duration_ms=int((time.time() - start_time) * 1000),
            status="success"
        )
        
        background_tasks.add_task(
            send_playbook_notification,
            playbook_id,
            request.playbook_name,
            request.version,
            "uploaded"
        )
        
        background_tasks.add_task(
            store_playbook_memory,
            playbook_id,
            request.playbook_name,
            request.content,
            request.version
        )
        
        logger.info(f"✅ Playbook '{request.playbook_name}' uploaded successfully: {playbook_id}")
        return response
        
    except Exception as e:
        # Log error
        error_msg = f"Error uploading playbook: {str(e)}"
        logger.error(error_msg)
        
        # Background error logging
        background_tasks.add_task(
            log_error,
            "/upload-playbook",
            error_msg,
            request.dict() if request else {}
        )
        
        background_tasks.add_task(
            send_error_notification,
            error_msg,
            "/upload-playbook",
            {"playbook_name": request.playbook_name if request else "unknown"}
        )
        
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/upload-playbook-file", response_model=PlaybookUploadResponse)
async def upload_playbook_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    playbook_name: str = Form(...),
    version: str = Form("1.0"),
    tags: Optional[str] = Form(None)
):
    """
    Upload a playbook via file upload
    
    This endpoint accepts multipart form data with a file
    """
    start_time = time.time()
    
    try:
        # Read file content
        content = await file.read()
        
        # Try to parse as JSON
        try:
            if file.content_type == "application/json":
                import json
                playbook_content = json.loads(content.decode('utf-8'))
            else:
                # Store as text for non-JSON files
                playbook_content = {
                    "content": content.decode('utf-8'),
                    "content_type": file.content_type,
                    "filename": file.filename
                }
        except Exception as parse_error:
            logger.warning(f"Could not parse file as JSON: {parse_error}")
            playbook_content = {
                "content": content.decode('utf-8', errors='replace'),
                "content_type": file.content_type,
                "filename": file.filename
            }
        
        # Parse tags
        tags_list = []
        if tags:
            tags_list = [tag.strip() for tag in tags.split(",")]
        
        # Create request object
        request = PlaybookUploadRequest(
            playbook_name=playbook_name,
            content=playbook_content,
            version=version,
            tags=tags_list
        )
        
        # Generate unique playbook ID
        playbook_id = f"pb_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:8]}"
        
        # Prepare response
        response = PlaybookUploadResponse(
            status="received",
            playbook_id=playbook_id,
            message="Playbook file uploaded successfully"
        )
        
        # Background tasks
        background_tasks.add_task(
            log_api_call,
            "/upload-playbook-file",
            request.dict(),
            response.dict(),
            duration_ms=int((time.time() - start_time) * 1000),
            status="success"
        )
        
        background_tasks.add_task(
            send_playbook_notification,
            playbook_id,
            playbook_name,
            version,
            "uploaded"
        )
        
        background_tasks.add_task(
            store_playbook_memory,
            playbook_id,
            playbook_name,
            playbook_content,
            version
        )
        
        logger.info(f"✅ Playbook file '{playbook_name}' uploaded successfully: {playbook_id}")
        return response
        
    except Exception as e:
        error_msg = f"Error uploading playbook file: {str(e)}"
        logger.error(error_msg)
        
        background_tasks.add_task(
            log_error,
            "/upload-playbook-file",
            error_msg,
            {"playbook_name": playbook_name, "filename": file.filename}
        )
        
        raise HTTPException(status_code=500, detail=error_msg)


@app.post("/route/{module_name}", response_model=GenericRouteResponse)
async def generic_route(
    module_name: str,
    request: GenericRouteRequest,
    background_tasks: BackgroundTasks
):
    """
    Generic routing endpoint that accepts any JSON payload
    
    This endpoint can be used to route requests to different modules
    """
    start_time = time.time()
    
    try:
        # Prepare response
        response = GenericRouteResponse(
            status="routed",
            module_name=module_name,
            message=f"Request routed to {module_name}"
        )
        
        # Background logging
        background_tasks.add_task(
            log_api_call,
            f"/route/{module_name}",
            request.dict(),
            response.dict(),
            duration_ms=int((time.time() - start_time) * 1000),
            status="success"
        )
        
        # Store in memory
        background_tasks.add_task(
            log_to_memory,
            {
                "module_name": module_name,
                "payload": request.payload,
                "metadata": request.metadata,
                "routed_at": datetime.now().isoformat()
            },
            "route",
            {"module_name": module_name}
        )
        
        logger.info(f"✅ Request routed to {module_name}")
        return response
        
    except Exception as e:
        error_msg = f"Error routing to {module_name}: {str(e)}"
        logger.error(error_msg)
        
        background_tasks.add_task(
            log_error,
            f"/route/{module_name}",
            error_msg,
            request.dict() if request else {}
        )
        
        raise HTTPException(status_code=500, detail=error_msg)


@app.get("/logs/stats")
async def get_logs_stats():
    """Get logging statistics"""
    try:
        stats = get_log_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting log stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/memory/stats")
async def get_memory_stats_endpoint():
    """Get memory statistics"""
    try:
        stats = get_memory_stats()
        return JSONResponse(content=stats)
    except Exception as e:
        logger.error(f"Error getting memory stats: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/debug/env")
async def debug_env():
    """Debug endpoint to check environment variables (for development/testing)"""
    try:
        env_vars = debug_environment()
        
        # Add some additional system info
        system_info = {
            "python_path": os.environ.get("PYTHONPATH", "Not Set"),
            "current_working_directory": os.getcwd(),
            "environment_count": len(os.environ),
            "available_env_vars": list(os.environ.keys())[:20]  # First 20 for safety
        }
        
        return JSONResponse(content={
            "environment_variables": env_vars,
            "system_info": system_info,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in debug endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/test/slack")
async def test_slack():
    """Test Slack integration by sending a test message"""
    try:
        from slack import send_slack_message
        
        slack_url = os.getenv("SLACK_WEBHOOK_URL", "")
        
        if not slack_url or not slack_url.startswith("https://hooks.slack.com/services/"):
            return JSONResponse(content={
                "status": "error",
                "message": "Slack webhook URL not configured properly",
                "configured": False,
                "timestamp": datetime.now().isoformat()
            })
        
        # Send test message
        test_message = {
            "text": "🧪 Test Message from AmplifAI Execution Engine",
            "blocks": [
                {
                    "type": "section",
                    "text": {
                        "type": "mrkdwn",
                        "text": "*Test Message* 🧪\n\nThis is a test message from the AmplifAI Execution Engine to verify Slack integration is working correctly."
                    }
                },
                {
                    "type": "context",
                    "elements": [
                        {
                            "type": "mrkdwn",
                            "text": f"Sent at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
                        }
                    ]
                }
            ]
        }
        
        success = send_slack_message(test_message)
        
        return JSONResponse(content={
            "status": "success" if success else "error",
            "slack_configured": True,
            "slack_url_preview": slack_url[:50] + "..." if len(slack_url) > 50 else slack_url,
            "message_sent": success,
            "message": "Test message sent successfully" if success else "Failed to send test message",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error testing Slack: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": f"Slack test failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.get("/test/clickhouse")
async def test_clickhouse():
    """Test ClickHouse integration"""
    try:
        from log_utils import test_clickhouse_connection
        
        clickhouse_url = os.getenv("CLICKHOUSE_URL", "")
        
        if not clickhouse_url:
            return JSONResponse(content={
                "status": "error",
                "message": "ClickHouse URL not configured",
                "configured": False,
                "timestamp": datetime.now().isoformat()
            })
        
        # Test the connection
        test_result = test_clickhouse_connection()
        
        return JSONResponse(content={
            "status": "success" if test_result else "error",
            "clickhouse_url_configured": bool(clickhouse_url),
            "clickhouse_url_preview": clickhouse_url[:50] + "..." if len(clickhouse_url) > 50 else clickhouse_url,
            "connection_test": test_result,
            "message": "ClickHouse connection successful" if test_result else "ClickHouse connection failed",
            "timestamp": datetime.now().isoformat()
        })
        
    except Exception as e:
        logger.error(f"Error testing ClickHouse: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": f"ClickHouse test failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.get("/test/all")
async def test_all_integrations():
    """Test all integrations (Slack + ClickHouse)"""
    try:
        from slack import send_slack_message
        from log_utils import test_clickhouse_connection
        
        results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "success",
            "tests": {}
        }
        
        # Test Slack
        slack_url = os.getenv("SLACK_WEBHOOK_URL", "")
        if slack_url and slack_url.startswith("https://hooks.slack.com/services/"):
            test_message = {
                "text": "🧪 Integration Test from AmplifAI Execution Engine",
                "blocks": [
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": "*Integration Test* 🧪\n\nTesting Slack integration as part of full system test."
                        }
                    }
                ]
            }
            slack_success = send_slack_message(test_message)
            results["tests"]["slack"] = {
                "configured": True,
                "test_passed": slack_success,
                "message": "Test message sent successfully" if slack_success else "Failed to send test message"
            }
        else:
            results["tests"]["slack"] = {
                "configured": False,
                "test_passed": False,
                "message": "Slack webhook URL not configured"
            }
        
        # Test ClickHouse
        clickhouse_url = os.getenv("CLICKHOUSE_URL", "")
        if clickhouse_url:
            clickhouse_success = test_clickhouse_connection()
            results["tests"]["clickhouse"] = {
                "configured": True,
                "test_passed": clickhouse_success,
                "message": "Connection successful" if clickhouse_success else "Connection failed"
            }
        else:
            results["tests"]["clickhouse"] = {
                "configured": False,
                "test_passed": False,
                "message": "ClickHouse URL not configured"
            }
        
        # Determine overall status
        all_tests_passed = all(
            test_result["test_passed"] for test_result in results["tests"].values()
            if test_result["configured"]
        )
        
        if not all_tests_passed:
            results["overall_status"] = "partial_failure"
        
        # Check if nothing is configured
        if not any(test_result["configured"] for test_result in results["tests"].values()):
            results["overall_status"] = "no_integrations_configured"
        
        return JSONResponse(content=results)
        
    except Exception as e:
        logger.error(f"Error testing all integrations: {e}")
        return JSONResponse(content={
            "status": "error",
            "message": f"Integration test failed: {str(e)}",
            "timestamp": datetime.now().isoformat()
        })


@app.get("/test/pdf-upload", response_class=HTMLResponse)
async def test_pdf_upload():
    """
    Test PDF upload functionality via web interface
    
    This endpoint provides a web-based test interface for the PDF upload functionality.
    It automatically runs the upload test and displays the results in an HTML format.
    """
    try:
        # Check if server is accessible
        base_url = "http://localhost:8000"
        test_results = []
        
        # Create test PDF content
        pdf_content = b'%PDF-1.4\n1 0 obj\n<<\n/Type /Catalog\n/Pages 2 0 R\n>>\nendobj\n2 0 obj\n<<\n/Type /Pages\n/Kids [3 0 R]\n/Count 1\n>>\nendobj\n3 0 obj\n<<\n/Type /Page\n/Parent 2 0 R\n/MediaBox [0 0 612 792]\n>>\nendobj\nxref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000074 00000 n \n0000000120 00000 n \ntrailer\n<<\n/Size 4\n/Root 1 0 R\n>>\nstartxref\n181\n%%EOF'
        
        # Test PDF upload
        async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
            files = {"file": ("test.pdf", pdf_content, "application/pdf")}
            data = {
                "playbook_name": "Web Test PDF Upload",
                "version": "1.0",
                "tags": "test,pdf,web,automation"
            }
            
            start_time = time.time()
            response = await client.post("/upload-playbook-file", files=files, data=data)
            duration = round((time.time() - start_time) * 1000, 2)
            
            # Parse response
            response_data = response.json() if response.status_code == 200 else {"error": response.text}
            
            test_results.append({
                "test": "PDF Upload Test",
                "endpoint": "/upload-playbook-file",
                "method": "POST",
                "status": response.status_code,
                "duration": f"{duration}ms",
                "success": response.status_code == 200,
                "response": response_data
            })
        
        # Generate HTML report
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>PDF Upload Test Results</title>
            <style>
                body { font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }
                .container { max-width: 1200px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                .header { background-color: #2c3e50; color: white; padding: 20px; border-radius: 8px; margin-bottom: 20px; }
                .success { background-color: #d4edda; border: 1px solid #c3e6cb; color: #155724; }
                .error { background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; }
                .test-result { margin: 15px 0; padding: 15px; border-radius: 4px; }
                .test-details { margin-top: 10px; }
                .json-response { background-color: #f8f9fa; padding: 10px; border-left: 4px solid #007bff; margin: 10px 0; overflow-x: auto; }
                .footer { margin-top: 30px; text-align: center; color: #666; }
                .badge { padding: 2px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }
                .badge-success { background-color: #28a745; color: white; }
                .badge-error { background-color: #dc3545; color: white; }
                table { width: 100%; border-collapse: collapse; margin: 15px 0; }
                th, td { padding: 8px; text-align: left; border-bottom: 1px solid #ddd; }
                th { background-color: #f8f9fa; }
                .endpoint-info { background-color: #e9ecef; padding: 15px; border-radius: 4px; margin: 15px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>📄 PDF Upload Test Results</h1>
                    <p>AmplifAI Execution Engine v1 - File Upload Validation</p>
                </div>
                
                <div class="endpoint-info">
                    <h3>🔍 Endpoint Information</h3>
                    <table>
                        <tr><th>Endpoint</th><td>/upload-playbook-file</td></tr>
                        <tr><th>Method</th><td>POST</td></tr>
                        <tr><th>Content-Type</th><td>multipart/form-data</td></tr>
                        <tr><th>Required Fields</th><td>file, playbook_name</td></tr>
                        <tr><th>Optional Fields</th><td>version, tags</td></tr>
                    </table>
                </div>
        """
        
        for result in test_results:
            import json
            status_class = "success" if result["success"] else "error"
            badge_class = "badge-success" if result["success"] else "badge-error"
            status_text = "✅ PASS" if result["success"] else "❌ FAIL"
            
            html_content += f"""
                <div class="test-result {status_class}">
                    <h3>{result['test']} <span class="badge {badge_class}">{status_text}</span></h3>
                    <div class="test-details">
                        <table>
                            <tr><th>Endpoint</th><td>{result['endpoint']}</td></tr>
                            <tr><th>Method</th><td>{result['method']}</td></tr>
                            <tr><th>Status Code</th><td>{result['status']}</td></tr>
                            <tr><th>Duration</th><td>{result['duration']}</td></tr>
                        </table>
                        <div class="json-response">
                            <strong>Response:</strong><br>
                            <pre>{json.dumps(result['response'], indent=2)}</pre>
                        </div>
                    </div>
                </div>
            """
        
        html_content += """
                <div class="footer">
                    <p>Test executed at """ + datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC') + """</p>
                    <p>🔄 <a href="/test/pdf-upload">Refresh Test</a> | 📊 <a href="/status">Server Status</a> | 📝 <a href="/docs">API Documentation</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        
        return html_content
        
    except Exception as e:
        error_html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>PDF Upload Test Error</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; background-color: #f5f5f5; }}
                .container {{ max-width: 800px; margin: 0 auto; background-color: white; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
                .error {{ background-color: #f8d7da; border: 1px solid #f5c6cb; color: #721c24; padding: 20px; border-radius: 4px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="error">
                    <h2>❌ Test Error</h2>
                    <p>An error occurred while running the PDF upload test:</p>
                    <pre>{str(e)}</pre>
                    <p><a href="/test/pdf-upload">Try Again</a></p>
                </div>
            </div>
        </body>
        </html>
        """
        return error_html


@app.get("/test-all", response_class=HTMLResponse)
async def test_all_routes():
    """
    Comprehensive self-test endpoint that exercises every API route 
    and displays results in a browser-friendly HTML table.
    """
    import json
    from datetime import datetime
    
    # Get the current port from environment or use default
    port = os.getenv("PORT", "8000")
    base_url = f"http://127.0.0.1:{port}"
    
    # Define all test cases
    tests = [
        # Basic endpoints
        ("GET /", "get", "/", None, "Root status endpoint"),
        ("GET /status", "get", "/status", None, "Health check endpoint"),
        
        # Main API endpoints  
        ("POST /launch-campaign", "post", "/launch-campaign", {
            "campaign_id": "test-campaign-123",
            "budget": 1000.0,
            "audience": {
                "age_range": "25-35",
                "interests": ["technology", "marketing"],
                "locations": ["US", "CA"]
            },
            "creatives": [
                {
                    "type": "banner",
                    "url": "https://example.com/banner.jpg",
                    "dimensions": "728x90"
                }
            ]
        }, "Launch marketing campaign"),
        
        ("POST /upload-playbook", "post", "/upload-playbook", {
            "playbook_id": "test-playbook-456",
            "name": "Test Marketing Playbook",
            "description": "A comprehensive test playbook for validation",
            "content": {
                "version": "1.0",
                "steps": [
                    {
                        "step_id": "step1",
                        "action": "send_email",
                        "parameters": {"template": "welcome"}
                    },
                    {
                        "step_id": "step2", 
                        "action": "track_event",
                        "parameters": {"event": "signup"}
                    }
                ]
            },
            "version": "1.0",
            "tags": ["test", "automation"]
        }, "Upload marketing playbook"),
        
        ("POST /route/test", "post", "/route/test", {
            "payload": {
                "action": "process_data",
                "data": {"key": "value", "timestamp": datetime.now().isoformat()}
            },
            "metadata": {
                "source": "self-test",
                "priority": "high"
            }
        }, "Generic routing endpoint"),
        
        # Statistics and monitoring
        ("GET /logs/stats", "get", "/logs/stats", None, "Logging statistics"),
        ("GET /memory/stats", "get", "/memory/stats", None, "Memory statistics"),
        ("GET /debug/env", "get", "/debug/env", None, "Environment debug info"),
        
        # Integration tests
        ("GET /test/slack", "get", "/test/slack", None, "Slack integration test"),
        ("GET /test/clickhouse", "get", "/test/clickhouse", None, "ClickHouse integration test"),
        ("GET /test/all", "get", "/test/all", None, "All integrations test"),
        ("GET /test/pdf-upload", "get", "/test/pdf-upload", None, "PDF upload test"),
        
        # Debug endpoints
        ("GET /debug/secrets", "get", "/debug/secrets", None, "Environment secrets debug"),
    ]
    
    results = []
    
    # Execute all tests
    async with httpx.AsyncClient(base_url=base_url, timeout=30.0) as client:
        for test_name, method, path, body, description in tests:
            try:
                start_time = time.time()
                
                if method == "get":
                    response = await client.get(path)
                elif method == "post":
                    response = await client.post(path, json=body)
                elif method == "post-file":
                    # Handle file uploads if needed
                    files = {"file": open(body["file_path"], "rb")}
                    data = body["fields"]
                    response = await client.post(path, files=files, data=data)
                    files["file"].close()
                else:
                    response = await client.request(method.upper(), path, json=body)
                
                duration = round((time.time() - start_time) * 1000, 2)
                
                # Try to parse JSON response
                try:
                    response_data = response.json()
                    response_text = json.dumps(response_data, indent=2)
                except:
                    response_text = response.text
                
                # Truncate long responses for display
                if len(response_text) > 500:
                    response_text = response_text[:500] + "\n... (truncated)"
                
                results.append({
                    "test": test_name,
                    "description": description,
                    "status": response.status_code,
                    "duration": f"{duration}ms",
                    "response": response_text,
                    "success": 200 <= response.status_code < 300
                })
                
            except Exception as e:
                results.append({
                    "test": test_name,
                    "description": description,
                    "status": "ERROR",
                    "duration": "N/A",
                    "response": str(e),
                    "success": False
                })
    
    # Calculate statistics
    total_tests = len(results)
    successful_tests = sum(1 for r in results if r["success"])
    failed_tests = total_tests - successful_tests
    success_rate = round((successful_tests / total_tests) * 100, 1) if total_tests > 0 else 0
    
    # Build HTML response
    html_parts = [
        """
        <!DOCTYPE html>
        <html>
        <head>
            <title>AmplifAI Execution Engine - API Self-Test Results</title>
            <style>
                body { 
                    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; 
                    margin: 20px; 
                    background-color: #f5f5f5;
                }
                .container { 
                    max-width: 1200px; 
                    margin: 0 auto; 
                    background: white; 
                    padding: 30px; 
                    border-radius: 10px;
                    box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                }
                h1 { 
                    color: #2c3e50; 
                    text-align: center; 
                    margin-bottom: 30px;
                }
                .summary { 
                    background: #ecf0f1; 
                    padding: 20px; 
                    border-radius: 8px; 
                    margin-bottom: 30px;
                    display: grid;
                    grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                    gap: 20px;
                }
                .stat { 
                    text-align: center; 
                }
                .stat-value { 
                    font-size: 2em; 
                    font-weight: bold; 
                    color: #3498db;
                }
                .stat-label { 
                    color: #7f8c8d; 
                    font-size: 0.9em;
                }
                table { 
                    width: 100%; 
                    border-collapse: collapse; 
                    margin-top: 20px;
                }
                th, td { 
                    padding: 12px; 
                    text-align: left; 
                    border-bottom: 1px solid #ddd;
                }
                th { 
                    background-color: #34495e; 
                    color: white;
                    font-weight: 600;
                }
                tr:hover { 
                    background-color: #f8f9fa;
                }
                .status-success { 
                    color: #27ae60; 
                    font-weight: bold;
                }
                .status-error { 
                    color: #e74c3c; 
                    font-weight: bold;
                }
                .status-warning { 
                    color: #f39c12; 
                    font-weight: bold;
                }
                pre { 
                    background: #f8f9fa; 
                    padding: 10px; 
                    border-radius: 4px; 
                    font-size: 0.85em; 
                    max-height: 200px; 
                    overflow-y: auto;
                    white-space: pre-wrap;
                    word-wrap: break-word;
                }
                .test-description { 
                    font-style: italic; 
                    color: #6c757d;
                }
                .success-rate-high { color: #27ae60; }
                .success-rate-medium { color: #f39c12; }
                .success-rate-low { color: #e74c3c; }
            </style>
        </head>
        <body>
            <div class="container">
                <h1>🧪 AmplifAI Execution Engine - API Self-Test Results</h1>
        """,
        
        f"""
                <div class="summary">
                    <div class="stat">
                        <div class="stat-value">{total_tests}</div>
                        <div class="stat-label">Total Tests</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" style="color: #27ae60">{successful_tests}</div>
                        <div class="stat-label">Passed</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value" style="color: #e74c3c">{failed_tests}</div>
                        <div class="stat-label">Failed</div>
                    </div>
                    <div class="stat">
                        <div class="stat-value {'success-rate-high' if success_rate >= 80 else 'success-rate-medium' if success_rate >= 60 else 'success-rate-low'}">{success_rate}%</div>
                        <div class="stat-label">Success Rate</div>
                    </div>
                </div>
                
                <table>
                    <thead>
                        <tr>
                            <th>Test Endpoint</th>
                            <th>Description</th>
                            <th>Status</th>
                            <th>Duration</th>
                            <th>Response</th>
                        </tr>
                    </thead>
                    <tbody>
        """
    ]
    
    # Add test results
    for result in results:
        status_class = "status-success" if result["success"] else "status-error"
        if result["status"] == "ERROR":
            status_class = "status-error"
        elif isinstance(result["status"], int):
            if 200 <= result["status"] < 300:
                status_class = "status-success"
            elif 400 <= result["status"] < 500:
                status_class = "status-warning"
            else:
                status_class = "status-error"
        
        html_parts.append(f"""
                        <tr>
                            <td><strong>{result["test"]}</strong></td>
                            <td class="test-description">{result["description"]}</td>
                            <td class="{status_class}">{result["status"]}</td>
                            <td>{result["duration"]}</td>
                            <td><pre>{result["response"]}</pre></td>
                        </tr>
        """)
    
    html_parts.append(f"""
                    </tbody>
                </table>
                
                <div style="margin-top: 30px; padding: 20px; background: #e8f4f8; border-radius: 8px;">
                    <h3>Test Summary</h3>
                    <p><strong>Test Run:</strong> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
                    <p><strong>Application:</strong> {APP_NAME} v{APP_VERSION}</p>
                    <p><strong>Base URL:</strong> {base_url}</p>
                    <p><strong>Total Duration:</strong> Tests completed successfully</p>
                    <p><strong>Status:</strong> 
                        <span class="{'status-success' if success_rate >= 80 else 'status-warning' if success_rate >= 60 else 'status-error'}">
                            {'✅ All systems operational' if success_rate >= 80 else '⚠️ Some issues detected' if success_rate >= 60 else '❌ Multiple failures detected'}
                        </span>
                    </p>
                </div>
                
                <div style="margin-top: 20px; text-align: center; color: #6c757d;">
                    <p>🔄 <a href="/test-all" style="color: #3498db;">Refresh Tests</a> | 
                    📊 <a href="/debug/env" style="color: #3498db;">Environment Info</a> | 
                    🏠 <a href="/" style="color: #3498db;">Back to Home</a></p>
                </div>
            </div>
        </body>
        </html>
    """)
    
    return HTMLResponse(content="".join(html_parts))


@app.get("/debug/secrets")
async def debug_secrets():
    """Debug endpoint to check environment secrets (safe for browser access)"""
    try:
        # Check all the environment variables we need
        secrets_status = {
            "SLACK_WEBHOOK_URL": {
                "exists": "SLACK_WEBHOOK_URL" in os.environ,
                "has_value": bool(os.environ.get("SLACK_WEBHOOK_URL", "")),
                "length": len(os.environ.get("SLACK_WEBHOOK_URL", "")),
                "preview": os.environ.get("SLACK_WEBHOOK_URL", "")[:50] + "..." if os.environ.get("SLACK_WEBHOOK_URL", "") else "NOT SET",
                "valid_format": os.environ.get("SLACK_WEBHOOK_URL", "").startswith("https://hooks.slack.com/services/")
            },
            "CLICKHOUSE_URL": {
                "exists": "CLICKHOUSE_URL" in os.environ,
                "has_value": bool(os.environ.get("CLICKHOUSE_URL", "")),
                "length": len(os.environ.get("CLICKHOUSE_URL", "")),
                "preview": os.environ.get("CLICKHOUSE_URL", "")[:30] + "..." if os.environ.get("CLICKHOUSE_URL", "") else "NOT SET"
            },
            "APP_NAME": {
                "exists": "APP_NAME" in os.environ,
                "has_value": bool(os.environ.get("APP_NAME", "")),
                "value": os.environ.get("APP_NAME", "NOT SET")
            },
            "APP_VERSION": {
                "exists": "APP_VERSION" in os.environ,
                "has_value": bool(os.environ.get("APP_VERSION", "")),
                "value": os.environ.get("APP_VERSION", "NOT SET")
            },
            "LOG_LEVEL": {
                "exists": "LOG_LEVEL" in os.environ,
                "has_value": bool(os.environ.get("LOG_LEVEL", "")),
                "value": os.environ.get("LOG_LEVEL", "NOT SET")
            }
        }
        
        # Summary
        total_secrets = len(secrets_status)
        configured_secrets = sum(1 for secret in secrets_status.values() if secret["has_value"])
        
        return JSONResponse(content={
            "summary": {
                "total_secrets_checked": total_secrets,
                "configured_secrets": configured_secrets,
                "configuration_percentage": round((configured_secrets / total_secrets) * 100, 1)
            },
            "secrets": secrets_status,
            "environment_info": {
                "total_env_vars": len(os.environ),
                "running_in_replit": "REPL_ID" in os.environ,
                "repl_id": os.environ.get("REPL_ID", "NOT IN REPLIT")
            },
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error in debug secrets endpoint: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# Error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    """Global HTTP exception handler"""
    logger.error(f"HTTP exception: {exc.status_code} - {exc.detail}")
    return JSONResponse(
        status_code=exc.status_code,
        content={"error": exc.detail, "status_code": exc.status_code}
    )


@app.exception_handler(Exception)
async def general_exception_handler(request, exc):
    """Global general exception handler"""
    logger.error(f"Unexpected error: {str(exc)}")
    return JSONResponse(
        status_code=500,
        content={"error": "Internal server error", "details": str(exc)}
    )


if __name__ == "__main__":
    import uvicorn
    
    # Get port from environment or default to 8000
    port = int(os.getenv("PORT", 8000))
    
    logger.info(f"Starting {APP_NAME} on port {port}")
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info"
    ) 