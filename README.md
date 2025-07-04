# AmplifAI Execution Engine v1

A powerful FastAPI-based execution engine for campaign management, playbook automation, and intelligent routing. Built with modern Python practices and designed for scalability.

## 🚀 Features

- **Campaign Management**: Launch and manage marketing campaigns with budget allocation and audience targeting
- **Playbook Automation**: Upload and process automation playbooks with JSON or file upload
- **Generic Routing**: Intelligent routing system for directing requests to appropriate modules
- **Comprehensive Logging**: Structured logging with ClickHouse simulation and file-based storage
- **Slack Integration**: Real-time notifications and updates via Slack webhooks
- **Memory Management**: Persistent storage with future Pinecone vector database integration
- **Health Monitoring**: Built-in health checks and performance monitoring
- **API Documentation**: Auto-generated OpenAPI/Swagger documentation

## 📋 Prerequisites

- Python 3.8 or higher
- pip (Python package manager)
- curl (for testing)

## 🛠️ Installation

### 1. Clone or Download the Project

```bash
git clone <repository-url>
cd "AmplifAI Execution Engine"
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
# On macOS/Linux:
source venv/bin/activate
# On Windows:
venv\Scripts\activate
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

### 4. Environment Configuration

Create a `.env` file in the project root:

```bash
cp .env.example .env
```

Edit the `.env` file with your configuration:

```env
# AmplifAI Execution Engine v1 Configuration
# Copy this file to .env and fill in your actual values

# Replit API Integration
REPLIT_API_KEY=your_replit_api_key_here

# ClickHouse Database Configuration
CLICKHOUSE_URL=https://your-clickhouse-instance.com

# Optional: Slack Webhook for Notifications
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Application Configuration
APP_NAME=AmplifAI Execution Engine v1
APP_VERSION=1.0.0
LOG_LEVEL=INFO
```

## 🚀 Quick Start

### 1. Start the Server

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

The server will start at `http://localhost:8000`

### 2. Access API Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

### 3. Test the API

```bash
# Quick health check
curl http://localhost:8000/status

# Run comprehensive tests
./tests/test_endpoints.sh
```

## 📖 API Endpoints

### Core Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| `GET` | `/` | Root endpoint with service information |
| `GET` | `/status` | Health check and uptime information |
| `POST` | `/launch-campaign` | Launch a marketing campaign |
| `POST` | `/upload-playbook` | Upload a playbook via JSON |
| `POST` | `/upload-playbook-file` | Upload a playbook via file |
| `POST` | `/route/{module_name}` | Generic routing endpoint |
| `GET` | `/logs/stats` | Get logging statistics |
| `GET` | `/memory/stats` | Get memory usage statistics |

### Campaign Launch

Launch a marketing campaign with budget allocation and targeting:

```bash
curl -X POST "http://localhost:8000/launch-campaign" \
  -H "Content-Type: application/json" \
  -d '{
    "campaign_id": "camp_social_media_2024_001",
    "budget": 5000.00,
    "audience": ["tech_enthusiasts", "young_professionals"],
    "creatives": ["creative_video_001", "creative_banner_002"]
  }'
```

**Response:**
```json
{
  "status": "launched",
  "campaign_id": "camp_social_media_2024_001",
  "timestamp": "2024-01-01T12:00:00Z",
  "message": "Campaign launched successfully"
}
```

### Playbook Upload

Upload automation playbooks for campaign management:

```bash
curl -X POST "http://localhost:8000/upload-playbook" \
  -H "Content-Type: application/json" \
  -d '{
    "playbook_name": "Social Media Campaign Automation",
    "content": {
      "steps": [
        {"action": "analyze_audience", "parameters": {"demographics": ["age", "location"]}},
        {"action": "create_content", "parameters": {"platforms": ["instagram", "facebook"]}}
      ]
    },
    "version": "1.0",
    "tags": ["social_media", "automation"]
  }'
```

### Generic Routing

Route requests to different modules:

```bash
curl -X POST "http://localhost:8000/route/analytics" \
  -H "Content-Type: application/json" \
  -d '{
    "payload": {
      "action": "process_analytics",
      "data": {"metric": "engagement_rate", "value": 3.5}
    },
    "metadata": {
      "source": "external_api",
      "priority": "high"
    }
  }'
```

## 🧪 Testing

### Automated Testing

Run the comprehensive test suite:

```bash
# Run all tests
./tests/test_endpoints.sh

# Run specific test categories
./tests/test_endpoints.sh --basic           # Basic endpoint tests
./tests/test_endpoints.sh --concurrent      # Concurrent request tests
./tests/test_endpoints.sh --file            # File upload tests
./tests/test_endpoints.sh --performance     # Performance tests

# Test against different URL
./tests/test_endpoints.sh --url http://localhost:3000
```

### Manual Testing

Use the provided sample JSON files:

```bash
# Test campaign launch
curl -X POST "http://localhost:8000/launch-campaign" \
  -H "Content-Type: application/json" \
  -d @tests/launch_campaign.json

# Test playbook upload
curl -X POST "http://localhost:8000/upload-playbook" \
  -H "Content-Type: application/json" \
  -d @tests/upload_playbook.json
```

## 📊 Monitoring & Logging

### Logging

The application provides comprehensive logging:

- **Console Logging**: Real-time logs in the terminal
- **File Logging**: Structured logs in `logs/application.jsonl`
- **ClickHouse Integration**: Ready for production database integration

View logging statistics:
```bash
curl http://localhost:8000/logs/stats
```

### Memory Management

Monitor memory usage and stored data:

```bash
curl http://localhost:8000/memory/stats
```

Memory data is stored in `memory/memory_store.jsonl` with future Pinecone integration planned.

## 🔌 Integrations

### Slack Notifications

Configure Slack webhook in your `.env` file:

```env
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

The system will automatically send notifications for:
- Campaign launches
- Playbook uploads
- Error alerts
- System health updates

### Replit Integration

Configure Replit API key for webhook calls:

```env
REPLIT_API_KEY=your_replit_api_key_here
```

### Future Integrations

- **ClickHouse**: Production-ready database logging
- **Pinecone**: Vector database for semantic search
- **OpenAI**: AI-powered content generation
- **Analytics Platforms**: Google Analytics, Facebook Pixel

## 🏗️ Architecture

### Project Structure

```
AmplifAI Execution Engine/
├── main.py                 # FastAPI application
├── schemas.py              # Pydantic models
├── log_utils.py            # Logging utilities
├── slack.py                # Slack integration
├── memory_utils.py         # Memory management
├── requirements.txt        # Python dependencies
├── README.md              # This file
├── tests/                 # Test files
│   ├── launch_campaign.json
│   ├── upload_playbook.json
│   └── test_endpoints.sh
├── logs/                  # Log files (auto-created)
└── memory/                # Memory storage (auto-created)
```

### Key Components

1. **FastAPI Application** (`main.py`)
   - RESTful API endpoints
   - Background task processing
   - Error handling and validation

2. **Data Models** (`schemas.py`)
   - Pydantic models for request/response validation
   - JSON schema generation
   - Type safety

3. **Logging System** (`log_utils.py`)
   - Structured logging with JSON format
   - Multiple output destinations
   - Performance monitoring

4. **Slack Integration** (`slack.py`)
   - Webhook notifications
   - Rich message formatting
   - Error alerting

5. **Memory Management** (`memory_utils.py`)
   - Persistent data storage
   - Future vector database integration
   - Search and retrieval capabilities

## 🔧 Configuration

### Environment Variables

| Variable | Description | Required | Default |
|----------|-------------|----------|---------|
| `REPLIT_API_KEY` | Replit API key for webhook calls | No | `""` |
| `CLICKHOUSE_URL` | ClickHouse database URL | No | `""` |
| `SLACK_WEBHOOK_URL` | Slack webhook URL for notifications | No | `""` |
| `APP_NAME` | Application name | No | `AmplifAI Execution Engine v1` |
| `APP_VERSION` | Application version | No | `1.0.0` |
| `LOG_LEVEL` | Logging level | No | `INFO` |
| `PORT` | Server port | No | `8000` |

### Production Deployment

For production deployment, consider:

1. **Environment Variables**: Use secure credential management
2. **Database**: Configure real ClickHouse instance
3. **Monitoring**: Set up application monitoring
4. **Scaling**: Use multiple worker processes
5. **Security**: Implement authentication and HTTPS

Example production command:
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Run the test suite
6. Submit a pull request

## 📝 API Examples

### Campaign Launch with Full Features

```python
import requests

# Launch a comprehensive campaign
response = requests.post("http://localhost:8000/launch-campaign", json={
    "campaign_id": "camp_holiday_2024_001",
    "budget": 15000.00,
    "audience": [
        "holiday_shoppers",
        "gift_buyers",
        "premium_customers",
        "returning_customers"
    ],
    "creatives": [
        "video_holiday_promo",
        "banner_gift_guide",
        "carousel_product_showcase",
        "story_countdown_timer"
    ]
})

print(f"Campaign Status: {response.json()['status']}")
```

### Playbook Upload with Complex Automation

```python
import requests

# Upload a complex automation playbook
playbook_data = {
    "playbook_name": "E-commerce Holiday Campaign",
    "content": {
        "steps": [
            {
                "step": 1,
                "action": "audience_analysis",
                "parameters": {
                    "segments": ["new_customers", "repeat_customers"],
                    "behavioral_triggers": ["cart_abandonment", "purchase_history"]
                }
            },
            {
                "step": 2,
                "action": "content_personalization",
                "parameters": {
                    "dynamic_content": True,
                    "personalization_rules": [
                        {"condition": "cart_value > 100", "content": "premium_offer"},
                        {"condition": "first_time_visitor", "content": "welcome_discount"}
                    ]
                }
            }
        ],
        "success_metrics": {
            "conversion_rate": 5.0,
            "average_order_value": 150.0,
            "customer_lifetime_value": 500.0
        }
    },
    "version": "2.0",
    "tags": ["ecommerce", "holiday", "personalization"]
}

response = requests.post("http://localhost:8000/upload-playbook", json=playbook_data)
print(f"Playbook ID: {response.json()['playbook_id']}")
```

## 🔍 Troubleshooting

### Common Issues

1. **Server Won't Start**
   - Check if port 8000 is available
   - Verify Python version (3.8+)
   - Ensure dependencies are installed

2. **Import Errors**
   - Activate virtual environment
   - Reinstall dependencies: `pip install -r requirements.txt`

3. **Environment Variables Not Loading**
   - Check `.env` file exists and has correct syntax
   - Verify file permissions

4. **Slack Notifications Not Working**
   - Verify webhook URL is correct
   - Check network connectivity
   - Review Slack webhook configuration

### Debug Mode

Enable debug logging:
```bash
LOG_LEVEL=DEBUG uvicorn main:app --reload
```

### Health Check

Verify system components:
```bash
curl http://localhost:8000/status
curl http://localhost:8000/logs/stats
curl http://localhost:8000/memory/stats
```

## 📄 License

This project is licensed under the MIT License. See the LICENSE file for details.

## 🙏 Acknowledgments

- FastAPI for the excellent web framework
- Pydantic for data validation
- Uvicorn for ASGI server implementation
- The open-source community for inspiration and tools

---

**AmplifAI Execution Engine v1** - Built with ❤️ for modern campaign management and automation. 