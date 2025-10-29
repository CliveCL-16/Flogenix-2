"""
OpenAPI documentation configuration for Flogenix Enterprise API
"""

from fastapi.openapi.utils import get_openapi
from fastapi import FastAPI

def custom_openapi(app: FastAPI):
    if app.openapi_schema:
        return app.openapi_schema
    
    openapi_schema = get_openapi(
        title="Flogenix Enterprise API",
        version="2.0.0",
        description="""
# 🏥 Flogenix Enterprise Healthcare Claims Processing API

## Overview
Flogenix Enterprise is an AI-powered healthcare claims processing platform that automates the entire claims lifecycle using multi-agent artificial intelligence. Our API provides comprehensive endpoints for claim submission, processing, fraud detection, user management, and real-time notifications.

## Key Features

### 🤖 Multi-Agent AI Processing
- **Intake Agent**: Validates claim data and extracts entities
- **Eligibility Agent**: Verifies insurance coverage and provider credentials  
- **Clinical Review Agent**: Validates medical codes and treatment necessity
- **Fraud Detection Agent**: Advanced pattern analysis and risk scoring
- **Adjudication Agent**: Final decision synthesis with explainable reasoning

### 🔐 Enterprise Security
- **JWT Authentication**: Secure token-based authentication with refresh tokens
- **Two-Factor Authentication**: TOTP-based 2FA with QR code setup
- **Role-Based Access Control**: USER, PROCESSOR, ADMIN, SUPER_ADMIN roles
- **Comprehensive Audit Trails**: Full activity logging and monitoring
- **Data Protection**: Input validation, sanitization, and encryption

### 📊 Real-time Analytics
- **Processing Metrics**: Claims volume, approval rates, processing times
- **Fraud Analytics**: Risk patterns and prevention effectiveness  
- **Agent Performance**: AI processing success rates and confidence scores
- **Business Intelligence**: Revenue analysis and operational insights

### 🔔 Real-time Notifications
- **WebSocket Support**: Live notification delivery
- **Priority-based Alerts**: Critical, high, medium, and low priority levels
- **Category Filtering**: Claims, fraud, system, user, and performance notifications
- **Multi-channel Delivery**: In-app, email, and webhook notifications

## Authentication

All API endpoints require authentication except for health checks and some public endpoints. Use the `/auth/login` endpoint to obtain access tokens.

### Bearer Token Authentication
```http
Authorization: Bearer <your_access_token>
```

### Two-Factor Authentication
For enhanced security, admin users can enable 2FA:
1. Call `/auth/2fa/setup` to generate QR code
2. Scan with authenticator app
3. Include `totp_code` in login requests

## Rate Limiting

API endpoints are rate-limited to prevent abuse:
- **Standard Users**: 100 requests per minute
- **Processors**: 500 requests per minute  
- **Admins**: 1000 requests per minute
- **WebSocket**: 50 connections per user

## Error Handling

The API uses standard HTTP status codes and returns detailed error information:

```json
{
  "detail": "Error description",
  "error_code": "VALIDATION_ERROR",
  "timestamp": "2024-01-15T10:30:00Z",
  "request_id": "req_123456789"
}
```

## Pagination

List endpoints support pagination using `limit` and `offset` parameters:

```json
{
  "items": [...],
  "total": 150,
  "limit": 20,
  "offset": 0,
  "has_next": true
}
```

## WebSocket Endpoints

Real-time features use WebSocket connections:

- **Notifications**: `/api/ws/notifications?token=<jwt_token>`
- **Claim Processing**: `/api/ws/claims?token=<jwt_token>`
- **Agent Monitoring**: `/api/ws/agents?token=<jwt_token>` (Admin only)

## Data Models

### Claim Processing Flow
1. **Submission** → `POST /api/claims/submit`
2. **AI Processing** → `POST /api/claims/{id}/process`  
3. **Decision** → `GET /api/claims/{id}`
4. **Notifications** → WebSocket delivery

### User Roles and Permissions

| Role | Claims | Processing | User Mgmt | System Config |
|------|--------|------------|-----------|---------------|
| USER | Submit, View Own | ❌ | ❌ | ❌ |
| PROCESSOR | Submit, View All | ✅ | ❌ | ❌ |
| ADMIN | Submit, View All | ✅ | ✅ | ✅ |
| SUPER_ADMIN | Submit, View All | ✅ | ✅ | ✅ |

## Integration Examples

### Submit and Process Claim
```python
import requests

# Authenticate
auth_response = requests.post('/auth/login', json={
    'email_or_username': 'user@example.com',
    'password': 'secure_password'
})
token = auth_response.json()['access_token']

# Submit claim
claim_data = {
    'patient_name': 'John Doe',
    'patient_id': 'PAT123456',
    'insurance_provider': 'Blue Cross Blue Shield',
    'policy_number': 'BCBS789012',
    'diagnosis_code': 'Z00.00',
    'procedure_code': '99213',
    'claim_amount': 250.00,
    'service_date': '2024-01-15',
    'provider_name': 'Dr. Jane Smith',
    'provider_npi': '1234567890'
}

claim_response = requests.post('/api/claims/submit', 
    json=claim_data,
    headers={'Authorization': f'Bearer {token}'}
)
claim_id = claim_response.json()['claim_id']

# Process with AI
process_response = requests.post(f'/api/claims/{claim_id}/process',
    headers={'Authorization': f'Bearer {token}'}
)
```

### WebSocket Notifications
```javascript
const token = localStorage.getItem('access_token');
const ws = new WebSocket(`ws://api.flogenix.com/api/ws/notifications?token=${token}`);

ws.onmessage = (event) => {
    const notification = JSON.parse(event.data);
    console.log('New notification:', notification);
    
    // Handle different notification types
    switch(notification.category) {
        case 'fraud':
            showFraudAlert(notification);
            break;
        case 'claim':
            updateClaimStatus(notification);
            break;
        default:
            showGenericNotification(notification);
    }
};
```

## Support

- **Documentation**: https://docs.flogenix.com
- **API Reference**: https://api.flogenix.com/docs
- **Support Portal**: https://support.flogenix.com
- **Status Page**: https://status.flogenix.com

For enterprise support, contact: enterprise@flogenix.com
        """,
        routes=app.routes,
        servers=[
            {"url": "http://localhost:8000", "description": "Development server"},
            {"url": "https://api.flogenix.com", "description": "Production server"},
            {"url": "https://staging-api.flogenix.com", "description": "Staging server"}
        ],
        contact={
            "name": "Flogenix API Support",
            "url": "https://support.flogenix.com",
            "email": "api-support@flogenix.com"
        },
        license_info={
            "name": "Enterprise License",
            "url": "https://flogenix.com/enterprise-license"
        }
    )
    
    # Add security scheme
    openapi_schema["components"]["securitySchemes"] = {
        "BearerAuth": {
            "type": "http",
            "scheme": "bearer",
            "bearerFormat": "JWT",
            "description": "JWT access token obtained from /auth/login endpoint"
        }
    }
    
    # Add global security requirement
    openapi_schema["security"] = [{"BearerAuth": []}]
    
    # Add custom tags
    openapi_schema["tags"] = [
        {
            "name": "Authentication",
            "description": "User authentication, registration, and 2FA management"
        },
        {
            "name": "Enterprise Claims", 
            "description": "Advanced claim processing with multi-agent AI"
        },
        {
            "name": "Legacy Claims",
            "description": "Backward-compatible claim endpoints"
        },
        {
            "name": "Notifications",
            "description": "Real-time notification system and WebSocket connections"
        },
        {
            "name": "Administration",
            "description": "User management and system administration (Admin only)"
        },
        {
            "name": "Analytics",
            "description": "Business intelligence and performance metrics"
        },
        {
            "name": "Health",
            "description": "System health checks and monitoring"
        }
    ]
    
    # Add example responses
    openapi_schema["components"]["examples"] = {
        "ClaimSubmissionExample": {
            "summary": "Standard medical claim",
            "value": {
                "patient_name": "John Doe",
                "patient_id": "PAT123456", 
                "insurance_provider": "Blue Cross Blue Shield",
                "policy_number": "BCBS789012",
                "diagnosis_code": "Z00.00",
                "procedure_code": "99213", 
                "claim_amount": 250.00,
                "service_date": "2024-01-15",
                "provider_name": "Dr. Jane Smith",
                "provider_npi": "1234567890",
                "notes": "Annual wellness exam"
            }
        },
        "LoginExample": {
            "summary": "User login with email",
            "value": {
                "email_or_username": "user@example.com",
                "password": "secure_password123"
            }
        },
        "LoginWith2FAExample": {
            "summary": "Login with 2FA enabled",
            "value": {
                "email_or_username": "admin@example.com", 
                "password": "secure_password123",
                "totp_code": "123456"
            }
        },
        "NotificationExample": {
            "summary": "Fraud alert notification",
            "value": {
                "id": "notif-123",
                "type": "warning",
                "category": "fraud", 
                "title": "High-Risk Claim Detected",
                "message": "Claim CLM-2024-001 flagged with 87% fraud risk",
                "priority": "high",
                "read": False,
                "created_at": "2024-01-15T10:30:00Z",
                "action_url": "/admin/claims/CLM-2024-001",
                "action_label": "Review Claim"
            }
        }
    }
    
    app.openapi_schema = openapi_schema
    return app.openapi_schema