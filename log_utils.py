"""
Logging utilities for AmplifAI Execution Engine v1
Provides structured logging with ClickHouse simulation
"""

import json
import os
import logging
from datetime import datetime
from typing import Dict, Any, Optional
from pathlib import Path
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Configuration
CLICKHOUSE_URL = os.getenv("CLICKHOUSE_URL", "")
LOG_FILE_PATH = "logs/application.jsonl"
ENABLE_CONSOLE_LOGGING = True
ENABLE_FILE_LOGGING = True


def ensure_log_directory():
    """Ensure the logs directory exists"""
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)


def format_log_entry(data: Dict[str, Any]) -> Dict[str, Any]:
    """Format log entry with consistent structure"""
    
    # Ensure timestamp is present
    if "timestamp" not in data:
        data["timestamp"] = datetime.now().isoformat()
    
    # Ensure required fields
    formatted_entry = {
        "timestamp": data.get("timestamp"),
        "endpoint": data.get("endpoint", "unknown"),
        "payload": data.get("payload", {}),
        "result": data.get("result", {}),
        "session_id": data.get("session_id"),
        "user_id": data.get("user_id"),
        "status": data.get("status", "unknown"),
        "duration_ms": data.get("duration_ms"),
        "error": data.get("error"),
        "metadata": data.get("metadata", {})
    }
    
    # Remove None values
    formatted_entry = {k: v for k, v in formatted_entry.items() if v is not None}
    
    return formatted_entry


def log_to_console(data: Dict[str, Any]) -> None:
    """Log to console with structured format"""
    try:
        formatted_data = format_log_entry(data)
        logger.info(f"API_LOG: {json.dumps(formatted_data, indent=2)}")
    except Exception as e:
        logger.error(f"Error logging to console: {e}")


def log_to_file(data: Dict[str, Any]) -> None:
    """Log to JSON Lines file"""
    try:
        ensure_log_directory()
        formatted_data = format_log_entry(data)
        
        with open(LOG_FILE_PATH, "a") as f:
            f.write(json.dumps(formatted_data) + "\n")
            
    except Exception as e:
        logger.error(f"Error logging to file: {e}")


def log_to_clickhouse_real(data: Dict[str, Any]) -> bool:
    """
    Real ClickHouse logging implementation (for future use)
    Currently disabled - will be enabled when CLICKHOUSE_URL is configured
    """
    if not CLICKHOUSE_URL:
        logger.debug("ClickHouse URL not configured, skipping real ClickHouse logging")
        return False
    
    try:
        formatted_data = format_log_entry(data)
        
        # Example ClickHouse HTTP API call
        # This would need to be customized based on your ClickHouse schema
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AmplifAI-Execution-Engine/1.0"
        }
        
        # Convert to ClickHouse-compatible format
        clickhouse_data = {
            "timestamp": formatted_data["timestamp"],
            "endpoint": formatted_data["endpoint"],
            "payload": json.dumps(formatted_data["payload"]),
            "result": json.dumps(formatted_data["result"]),
            "session_id": formatted_data.get("session_id", ""),
            "user_id": formatted_data.get("user_id", ""),
            "status": formatted_data.get("status", ""),
            "duration_ms": formatted_data.get("duration_ms", 0),
            "error": formatted_data.get("error", ""),
            "metadata": json.dumps(formatted_data.get("metadata", {}))
        }
        
        # This is a placeholder - actual implementation would depend on your ClickHouse setup
        # response = requests.post(
        #     f"{CLICKHOUSE_URL}/api/logs",
        #     json=clickhouse_data,
        #     headers=headers,
        #     timeout=10
        # )
        # response.raise_for_status()
        
        logger.info(f"Would log to ClickHouse: {json.dumps(clickhouse_data, indent=2)}")
        return True
        
    except Exception as e:
        logger.error(f"Error logging to ClickHouse: {e}")
        return False


def log_to_clickhouse(data: Dict[str, Any]) -> bool:
    """
    Main logging function that simulates ClickHouse logging
    Falls back to console and file logging
    """
    success = True
    
    try:
        # Always log to console if enabled
        if ENABLE_CONSOLE_LOGGING:
            log_to_console(data)
        
        # Always log to file if enabled
        if ENABLE_FILE_LOGGING:
            log_to_file(data)
        
        # Attempt real ClickHouse logging if configured
        if CLICKHOUSE_URL:
            clickhouse_success = log_to_clickhouse_real(data)
            if not clickhouse_success:
                logger.warning("ClickHouse logging failed, but console/file logging succeeded")
        else:
            logger.info("ClickHouse URL not configured - using console/file logging only")
            
    except Exception as e:
        logger.error(f"Critical error in log_to_clickhouse: {e}")
        success = False
    
    return success


def create_log_entry(
    endpoint: str,
    payload: Dict[str, Any],
    result: Dict[str, Any],
    session_id: Optional[str] = None,
    user_id: Optional[str] = None,
    status: str = "success",
    duration_ms: Optional[int] = None,
    error: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Create a structured log entry
    """
    return {
        "timestamp": datetime.now().isoformat(),
        "endpoint": endpoint,
        "payload": payload,
        "result": result,
        "session_id": session_id,
        "user_id": user_id,
        "status": status,
        "duration_ms": duration_ms,
        "error": error,
        "metadata": metadata or {}
    }


def log_api_call(
    endpoint: str,
    request_data: Dict[str, Any],
    response_data: Dict[str, Any],
    **kwargs
) -> bool:
    """
    Convenience function for logging API calls
    """
    log_entry = create_log_entry(
        endpoint=endpoint,
        payload=request_data,
        result=response_data,
        **kwargs
    )
    
    return log_to_clickhouse(log_entry)


def log_error(
    endpoint: str,
    error_message: str,
    payload: Dict[str, Any],
    **kwargs
) -> bool:
    """
    Convenience function for logging errors
    """
    log_entry = create_log_entry(
        endpoint=endpoint,
        payload=payload,
        result={"error": error_message},
        status="error",
        error=error_message,
        **kwargs
    )
    
    return log_to_clickhouse(log_entry)


def get_log_stats() -> Dict[str, Any]:
    """
    Get basic statistics about logged entries
    """
    try:
        if not os.path.exists(LOG_FILE_PATH):
            return {"total_entries": 0, "file_exists": False}
        
        with open(LOG_FILE_PATH, "r") as f:
            lines = f.readlines()
            
        total_entries = len(lines)
        
        # Parse recent entries for basic stats
        recent_entries = []
        for line in lines[-10:]:  # Last 10 entries
            try:
                entry = json.loads(line.strip())
                recent_entries.append(entry)
            except json.JSONDecodeError:
                continue
        
        endpoints = [entry.get("endpoint") for entry in recent_entries]
        statuses = [entry.get("status") for entry in recent_entries]
        
        return {
            "total_entries": total_entries,
            "file_exists": True,
            "recent_endpoints": list(set(endpoints)),
            "recent_statuses": list(set(statuses)),
            "log_file_path": LOG_FILE_PATH
        }
        
    except Exception as e:
        logger.error(f"Error getting log stats: {e}")
        return {"error": str(e)}


# Example usage and testing
if __name__ == "__main__":
    # Test logging functionality
    test_data = {
        "endpoint": "/test",
        "payload": {"test": "data"},
        "result": {"status": "success"},
        "session_id": "test_session",
        "user_id": "test_user"
    }
    
    print("Testing logging functionality...")
    success = log_to_clickhouse(test_data)
    print(f"Logging test result: {'Success' if success else 'Failed'}")
    
    # Test log stats
    stats = get_log_stats()
    print(f"Log stats: {json.dumps(stats, indent=2)}") 