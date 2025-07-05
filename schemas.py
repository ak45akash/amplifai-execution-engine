"""
Pydantic Data Models for AmplifAI Execution Engine v1
======================================================

Comprehensive data validation and serialization schemas using Pydantic for
type safety, automatic validation, and API documentation generation. These
models define the structure and constraints for all API requests and responses.

Features:
- **Type Safety**: Automatic type checking and conversion
- **Data Validation**: Field validation with custom constraints
- **API Documentation**: Auto-generated OpenAPI/Swagger schemas
- **Serialization**: JSON encoding/decoding with proper formats
- **Error Handling**: Descriptive validation error messages

Model Categories:
1. **Campaign Models**: Campaign launch requests and responses
2. **Playbook Models**: Playbook upload and management schemas
3. **Routing Models**: Generic routing for dynamic endpoint handling
4. **System Models**: Health checks, status responses, and monitoring
5. **Integration Models**: Slack notifications and logging structures

Validation Features:
- Field constraints (min/max values, string lengths, required fields)
- Custom validators for business logic
- Nested model validation for complex objects
- Automatic documentation with examples
- Type coercion and error reporting

Usage Patterns:
- FastAPI endpoint parameter validation
- Response serialization and formatting
- Database model definitions
- API client generation
- Integration testing and mocking

Documentation:
Each model includes comprehensive examples and field descriptions
for automatic API documentation generation via OpenAPI/Swagger.

Created by: AmplifAI Team
Dependencies: pydantic, typing
Version: 1.0.0
"""

from pydantic import BaseModel, Field
from typing import List, Optional, Dict, Any
from datetime import datetime


class CampaignLaunchRequest(BaseModel):
    """
    Campaign Launch Request Model
    
    Defines the structure and validation rules for campaign launch requests.
    This model ensures data integrity and provides clear API documentation
    for client applications and automated testing.
    
    Validation Rules:
    - campaign_id: Must be unique string identifier (no special characters recommended)
    - budget: Must be positive number (>0) representing dollars
    - audience: At least one audience segment required
    - creatives: At least one creative asset required
    
    Business Logic:
    - Campaign IDs should follow naming conventions (e.g., "camp_social_2024_q1")
    - Budget amounts are in USD and should align with account limits
    - Audience segments should match predefined targeting categories
    - Creative IDs should reference existing assets in the creative library
    
    Integration:
    - Used by POST /launch-campaign endpoint
    - Validated automatically by FastAPI
    - Generates OpenAPI documentation
    - Supports JSON serialization for logging and storage
    """
    campaign_id: str = Field(
        ..., 
        description="Unique identifier for the campaign (e.g., 'social_media_2024_q1')",
        min_length=3,
        max_length=100,
        pattern=r"^[a-zA-Z0-9_-]+$"
    )
    budget: float = Field(
        ..., 
        gt=0, 
        description="Campaign budget in USD (must be positive)",
        example=15000.0
    )
    audience: List[str] = Field(
        ..., 
        min_items=1, 
        description="Target audience segments (at least one required)",
        example=["tech_enthusiasts", "young_professionals"]
    )
    creatives: List[str] = Field(
        ..., 
        min_items=1, 
        description="Creative asset IDs from the creative library",
        example=["video_promo_001", "banner_ad_002"]
    )

    class Config:
        json_schema_extra = {
            "example": {
                "campaign_id": "social_media_holiday_2024",
                "budget": 15000.0,
                "audience": ["holiday_shoppers", "tech_enthusiasts", "young_professionals"],
                "creatives": ["video_holiday_promo", "banner_gift_guide", "carousel_products"]
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