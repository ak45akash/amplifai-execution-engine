"""
Pydantic schemas for AmplifAI Execution Engine v1
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class CampaignLaunchRequest(BaseModel):
    """Request model for launching a campaign"""
    campaign_id: str = Field(..., description="Unique identifier for the campaign")
    budget: float = Field(..., gt=0, description="Campaign budget in dollars")
    audience: List[str] = Field(..., min_items=1, description="List of target audience segments")
    creatives: List[str] = Field(..., min_items=1, description="List of creative asset IDs")

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "camp_001",
                "budget": 5000.0,
                "audience": ["tech_enthusiasts", "young_professionals"],
                "creatives": ["creative_001", "creative_002"]
            }
        }


class CampaignLaunchResponse(BaseModel):
    """Response model for campaign launch"""
    status: str = Field(..., description="Launch status")
    campaign_id: str = Field(..., description="Campaign identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Launch timestamp")
    message: Optional[str] = Field(None, description="Additional message")


class PlaybookUploadRequest(BaseModel):
    """Request model for uploading a playbook"""
    playbook_name: str = Field(..., description="Name of the playbook")
    content: Dict[str, Any] = Field(..., description="Playbook content as JSON")
    version: Optional[str] = Field("1.0", description="Playbook version")
    tags: Optional[List[str]] = Field(default_factory=list, description="Playbook tags")

    class Config:
        json_schema_extra = {
            "example": {
                "playbook_name": "Social Media Campaign",
                "content": {
                    "steps": [
                        {"action": "create_post", "platform": "instagram"},
                        {"action": "schedule_post", "time": "9:00 AM"}
                    ]
                },
                "version": "1.0",
                "tags": ["social", "automated"]
            }
        }


class PlaybookUploadResponse(BaseModel):
    """Response model for playbook upload"""
    status: str = Field(..., description="Upload status")
    playbook_id: str = Field(..., description="Generated playbook identifier")
    timestamp: datetime = Field(default_factory=datetime.now, description="Upload timestamp")
    message: Optional[str] = Field(None, description="Additional message")


class StatusResponse(BaseModel):
    """Response model for health check"""
    status: str = Field(..., description="Service status")
    uptime: str = Field(..., description="Service uptime")
    timestamp: datetime = Field(default_factory=datetime.now, description="Current timestamp")
    version: str = Field("1.0.0", description="Application version")


class GenericRouteRequest(BaseModel):
    """Generic request model for dynamic routing"""
    payload: Dict[str, Any] = Field(..., description="Generic payload data")
    metadata: Optional[Dict[str, str]] = Field(default_factory=dict, description="Additional metadata")

    class Config:
        json_schema_extra = {
            "example": {
                "payload": {
                    "action": "process_data",
                    "data": {"key": "value"}
                },
                "metadata": {
                    "source": "external_api",
                    "priority": "high"
                }
            }
        }


class GenericRouteResponse(BaseModel):
    """Generic response model for dynamic routing"""
    status: str = Field(..., description="Route status")
    module_name: str = Field(..., description="Target module name")
    timestamp: datetime = Field(default_factory=datetime.now, description="Processing timestamp")
    message: str = Field(..., description="Processing message")


class LogEntry(BaseModel):
    """Model for log entries"""
    timestamp: datetime = Field(default_factory=datetime.now, description="Log timestamp")
    endpoint: str = Field(..., description="API endpoint")
    payload: Dict[str, Any] = Field(..., description="Request payload")
    result: Dict[str, Any] = Field(..., description="Response result")
    session_id: Optional[str] = Field(None, description="Session identifier")
    user_id: Optional[str] = Field(None, description="User identifier")

    class Config:
        json_schema_extra = {
            "example": {
                "timestamp": "2024-01-01T12:00:00Z",
                "endpoint": "/launch-campaign",
                "payload": {"campaign_id": "camp_001", "budget": 5000.0},
                "result": {"status": "launched", "campaign_id": "camp_001"},
                "session_id": "sess_001",
                "user_id": "user_001"
            }
        }


class SlackNotification(BaseModel):
    """Model for Slack notification"""
    text: str = Field(..., description="Notification message")
    channel: Optional[str] = Field(None, description="Slack channel")
    username: Optional[str] = Field("AmplifAI Bot", description="Bot username")
    emoji: Optional[str] = Field(":robot_face:", description="Bot emoji")

    class Config:
        json_schema_extra = {
            "example": {
                "text": "Campaign camp_001 launched successfully with budget $5000",
                "channel": "#campaigns",
                "username": "AmplifAI Bot",
                "emoji": ":rocket:"
            }
        } 