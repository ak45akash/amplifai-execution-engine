"""
AmplifAI Execution Engine v1
FastAPI application with campaign launch, playbook upload, and routing capabilities
"""

import os
import uuid
import time
import logging
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, File, UploadFile, Form, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import requests
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

# Load environment variables
# First try to load from .env file (for local development)
load_dotenv()

# Configuration with better debugging
REPLIT_API_KEY = os.getenv("REPLIT_API_KEY", "")
REPLIT_WEBHOOK_URL = os.getenv("REPLIT_WEBHOOK_URL", "https://api.replit.com/webhook/placeholder")
APP_NAME = os.getenv("APP_NAME", "AmplifAI Execution Engine v1")
APP_VERSION = os.getenv("APP_VERSION", "1.0.0")
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
CLICKHOUSE_URL = os.getenv("CLICKHOUSE_URL", "")

# Debug environment variables
def debug_environment():
    """Debug function to check environment variables"""
    env_vars = {
        "REPLIT_API_KEY": bool(os.getenv("REPLIT_API_KEY")),
        "SLACK_WEBHOOK_URL": bool(os.getenv("SLACK_WEBHOOK_URL")),
        "CLICKHOUSE_URL": bool(os.getenv("CLICKHOUSE_URL")),
        "APP_NAME": os.getenv("APP_NAME", "Not Set"),
        "APP_VERSION": os.getenv("APP_VERSION", "Not Set"),
        "PORT": os.getenv("PORT", "Not Set"),
    }
    
    logger.info("🔍 Environment Variables Debug:")
    for key, value in env_vars.items():
        if isinstance(value, bool):
            status = "✅ SET" if value else "❌ NOT SET"
            logger.info(f"  {key}: {status}")
        else:
            logger.info(f"  {key}: {value}")
    
    # Show first few characters of sensitive vars if they exist
    if os.getenv("REPLIT_API_KEY"):
        logger.info(f"  REPLIT_API_KEY preview: {os.getenv('REPLIT_API_KEY')[:8]}...")
    if os.getenv("SLACK_WEBHOOK_URL"):
        logger.info(f"  SLACK_WEBHOOK_URL preview: {os.getenv('SLACK_WEBHOOK_URL')[:30]}...")
    
    return env_vars

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Application startup time for uptime calculation
startup_time = datetime.now()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifecycle management"""
    logger.info(f"Starting {APP_NAME} v{APP_VERSION}")
    
    # Debug environment variables
    env_debug = debug_environment()
    
    # Check configurations with better logic
    replit_configured = bool(os.getenv("REPLIT_API_KEY"))
    slack_configured = is_slack_configured()
    
    logger.info(f"Replit API configured: {'✅ Yes' if replit_configured else '❌ No'}")
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


async def simulate_replit_webhook(campaign_data: Dict[str, Any]) -> bool:
    """
    Simulate a Replit webhook call
    In production, this would make an actual HTTP request to Replit
    """
    try:
        # Get the current API key value
        current_api_key = os.getenv("REPLIT_API_KEY")
        
        if not current_api_key:
            logger.warning("Replit API key not configured - simulating webhook call")
            webhook_data = {
                "api_key": "DEMO_KEY",
                "action": "launch_campaign",
                "campaign_id": campaign_data["campaign_id"],
                "budget": campaign_data["budget"],
                "audience": campaign_data["audience"],
                "creatives": campaign_data["creatives"],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"🔄 Simulated Replit webhook call: {webhook_data}")
            return True
        else:
            # Real webhook call (uncomment when ready)
            headers = {
                "Authorization": f"Bearer {current_api_key}",
                "Content-Type": "application/json"
            }
            
            webhook_data = {
                "action": "launch_campaign",
                "campaign_id": campaign_data["campaign_id"],
                "budget": campaign_data["budget"],
                "audience": campaign_data["audience"],
                "creatives": campaign_data["creatives"],
                "timestamp": datetime.now().isoformat()
            }
            
            logger.info(f"🔄 Would make real Replit webhook call to: {REPLIT_WEBHOOK_URL}")
            logger.info(f"📦 Webhook payload: {webhook_data}")
            
            # Uncomment for real webhook calls:
            # response = requests.post(
            #     REPLIT_WEBHOOK_URL,
            #     json=webhook_data,
            #     headers=headers,
            #     timeout=30
            # )
            # response.raise_for_status()
            
            return True
            
    except Exception as e:
        logger.error(f"Error in Replit webhook call: {e}")
        return False


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
    Launch a marketing campaign
    
    This endpoint:
    1. Validates the campaign request
    2. Simulates a Replit webhook call
    3. Logs the operation to ClickHouse
    4. Sends Slack notification (if configured)
    5. Stores campaign memory
    """
    start_time = time.time()
    
    try:
        campaign_data = request.dict()
        
        # Simulate Replit webhook call
        replit_success = await simulate_replit_webhook(campaign_data)
        
        if not replit_success:
            logger.error("Replit webhook simulation failed")
            # Don't fail the entire request - just log the issue
        
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