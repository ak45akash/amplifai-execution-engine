"""
Slack integration for AmplifAI Execution Engine v1
Provides webhook notifications and messaging capabilities
"""

import json
import os
import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
import requests
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger = logging.getLogger(__name__)

# Configuration
SLACK_WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL", "")
DEFAULT_CHANNEL = "#general"
DEFAULT_USERNAME = "AmplifAI Bot"
DEFAULT_EMOJI = ":robot_face:"
TIMEOUT_SECONDS = 10


def is_slack_configured() -> bool:
    """Check if Slack webhook is configured"""
    return bool(SLACK_WEBHOOK_URL)


def format_slack_message(
    message: str,
    channel: Optional[str] = None,
    username: Optional[str] = None,
    emoji: Optional[str] = None,
    color: Optional[str] = None,
    fields: Optional[List[Dict[str, Any]]] = None
) -> Dict[str, Any]:
    """
    Format a message for Slack webhook
    
    Args:
        message: Main message text
        channel: Slack channel (optional)
        username: Bot username (optional)
        emoji: Bot emoji (optional)
        color: Message color (good, warning, danger, or hex)
        fields: List of additional fields
    
    Returns:
        Formatted Slack payload
    """
    payload = {
        "text": message,
        "username": username or DEFAULT_USERNAME,
        "icon_emoji": emoji or DEFAULT_EMOJI
    }
    
    if channel:
        payload["channel"] = channel
    
    # Add rich formatting if specified
    if color or fields:
        attachment = {
            "color": color or "good",
            "text": message,
            "ts": int(datetime.now().timestamp())
        }
        
        if fields:
            attachment["fields"] = fields
        
        payload["attachments"] = [attachment]
        # Remove text from main payload since it's in attachment
        del payload["text"]
    
    return payload


def send_slack_webhook(payload: Dict[str, Any]) -> bool:
    """
    Send a message to Slack webhook
    
    Args:
        payload: Slack webhook payload
        
    Returns:
        True if successful, False otherwise
    """
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack webhook URL not configured")
        return False
    
    try:
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AmplifAI-Execution-Engine/1.0"
        }
        
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            headers=headers,
            timeout=TIMEOUT_SECONDS
        )
        
        response.raise_for_status()
        
        if response.text == "ok":
            logger.info("Slack notification sent successfully")
            return True
        else:
            logger.error(f"Slack webhook returned unexpected response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Slack notification: {e}")
        return False


def send_slack_notification(
    message: str,
    channel: Optional[str] = None,
    username: Optional[str] = None,
    emoji: Optional[str] = None
) -> bool:
    """Send a simple Slack notification"""
    if not SLACK_WEBHOOK_URL:
        logger.warning("Slack webhook URL not configured")
        return False
    
    try:
        payload = {
            "text": message,
            "username": username or DEFAULT_USERNAME,
            "icon_emoji": emoji or DEFAULT_EMOJI
        }
        
        if channel:
            payload["channel"] = channel
        
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "AmplifAI-Execution-Engine/1.0"
        }
        
        response = requests.post(
            SLACK_WEBHOOK_URL,
            json=payload,
            headers=headers,
            timeout=TIMEOUT_SECONDS
        )
        
        response.raise_for_status()
        
        if response.text == "ok":
            logger.info("Slack notification sent successfully")
            return True
        else:
            logger.error(f"Slack webhook returned unexpected response: {response.text}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"Failed to send Slack notification: {e}")
        return False
    except Exception as e:
        logger.error(f"Unexpected error sending Slack notification: {e}")
        return False


def send_campaign_notification(
    campaign_id: str,
    budget: float,
    audience: List[str],
    creatives: List[str],
    status: str = "launched"
) -> bool:
    """Send a campaign-specific notification"""
    try:
        message = f"🚀 Campaign {campaign_id} has been {status}!\n"
        message += f"💰 Budget: ${budget:,.2f}\n"
        message += f"🎯 Audience: {', '.join(audience)}\n"
        message += f"🎨 Creatives: {', '.join(creatives)}\n"
        message += f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        return send_slack_notification(message, emoji=":rocket:")
        
    except Exception as e:
        logger.error(f"Error in send_campaign_notification: {e}")
        return False


def send_playbook_notification(
    playbook_id: str,
    playbook_name: str,
    version: str = "1.0",
    status: str = "uploaded"
) -> bool:
    """Send a playbook-specific notification"""
    try:
        message = f"📚 Playbook '{playbook_name}' has been {status}!\n"
        message += f"🆔 ID: {playbook_id}\n"
        message += f"🏷️ Version: {version}\n"
        message += f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        return send_slack_notification(message, emoji=":books:")
        
    except Exception as e:
        logger.error(f"Error in send_playbook_notification: {e}")
        return False


def send_error_notification(
    error_message: str,
    endpoint: str,
    details: Optional[Dict[str, Any]] = None
) -> bool:
    """Send an error notification"""
    try:
        message = f"🚨 Error in {endpoint}: {error_message}\n"
        message += f"📅 Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S UTC')}"
        
        if details:
            message += f"\n📄 Details: {json.dumps(details, indent=2)}"
        
        return send_slack_notification(message, emoji=":warning:")
        
    except Exception as e:
        logger.error(f"Error in send_error_notification: {e}")
        return False


def send_health_check_notification(
    status: str,
    uptime: str,
    additional_info: Optional[Dict[str, Any]] = None
) -> bool:
    """
    Send a health check notification
    
    Args:
        status: Service status
        uptime: Service uptime
        additional_info: Additional service information
        
    Returns:
        True if successful, False otherwise
    """
    try:
        message = f"🏥 Health Check: Service is {status}"
        
        fields = [
            {
                "title": "Status",
                "value": status.upper(),
                "short": True
            },
            {
                "title": "Uptime",
                "value": uptime,
                "short": True
            },
            {
                "title": "Timestamp",
                "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "short": False
            }
        ]
        
        if additional_info:
            for key, value in additional_info.items():
                fields.append({
                    "title": key.title(),
                    "value": str(value),
                    "short": True
                })
        
        color = "good" if status.lower() == "ok" else "warning"
        
        payload = format_slack_message(
            message=message,
            emoji=":heart:",
            color=color,
            fields=fields
        )
        
        return send_slack_webhook(payload)
        
    except Exception as e:
        logger.error(f"Error in send_health_check_notification: {e}")
        return False


def test_slack_integration() -> bool:
    """
    Test Slack integration with a simple message
    
    Returns:
        True if successful, False otherwise
    """
    try:
        test_message = "🧪 Test notification from AmplifAI Execution Engine v1"
        
        fields = [
            {
                "title": "Test Status",
                "value": "PASS",
                "short": True
            },
            {
                "title": "Timestamp",
                "value": datetime.now().strftime("%Y-%m-%d %H:%M:%S UTC"),
                "short": True
            }
        ]
        
        payload = format_slack_message(
            message=test_message,
            emoji=":test_tube:",
            color="good",
            fields=fields
        )
        
        return send_slack_webhook(payload)
        
    except Exception as e:
        logger.error(f"Error in test_slack_integration: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    print("Testing Slack integration...")
    
    if not is_slack_configured():
        print("⚠️  Slack webhook URL not configured")
        print("Set SLACK_WEBHOOK_URL in your .env file to test Slack integration")
    else:
        print("✅ Slack webhook URL configured")
        
        # Test simple notification
        print("Testing simple notification...")
        success = send_slack_notification(
            message="Hello from AmplifAI Execution Engine v1!",
            emoji=":wave:"
        )
        print(f"Simple notification test: {'✅ Success' if success else '❌ Failed'}")
        
        # Test campaign notification
        print("Testing campaign notification...")
        success = send_campaign_notification(
            campaign_id="test_campaign_001",
            budget=1000.0,
            audience=["test_audience_1", "test_audience_2"],
            creatives=["creative_001", "creative_002"],
            status="launched"
        )
        print(f"Campaign notification test: {'✅ Success' if success else '❌ Failed'}")
        
        # Test error notification
        print("Testing error notification...")
        success = send_error_notification(
            error_message="Test error message",
            endpoint="/test-endpoint",
            details={"error_code": "TEST_001", "severity": "low"}
        )
        print(f"Error notification test: {'✅ Success' if success else '❌ Failed'}")
    
    print("Slack integration testing completed!") 