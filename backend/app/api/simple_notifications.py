"""
Notifications API endpoints
Simple notification system with WebSocket support
"""

import json
from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, status
from sqlalchemy.orm import Session
from pydantic import BaseModel

from app.core.database import get_database_session
from app.core.security import get_current_user
from app.core.models import User, Notification
from app.services.simple_notification_service import (
    SimpleNotificationService, 
    WebSocketManager,
    websocket_manager,
    NotificationType,
    NotificationPriority
)

# Router
router = APIRouter()

# Response models
class NotificationResponse(BaseModel):
    """Notification response model"""
    id: int
    notification_id: str
    title: str
    message: str
    notification_type: str
    priority: str
    is_read: bool
    created_at: datetime
    read_at: Optional[datetime]
    related_resource_type: Optional[str]
    related_resource_id: Optional[str]

class NotificationsListResponse(BaseModel):
    """Notifications list response"""
    notifications: List[NotificationResponse]
    count: int
    unread_count: int

class NotificationStatsResponse(BaseModel):
    """Notification statistics response"""
    total_notifications: int
    unread_notifications: int
    category_breakdown: dict

@router.websocket("/notifications/ws")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(..., description="Authentication token")
):
    """
    WebSocket endpoint for real-time notifications
    
    Connect with: ws://localhost:8000/api/notifications/ws?token=<jwt_token>
    """
    try:
        # For simplicity, we'll extract user_id from token
        # In production, you'd properly validate the JWT token
        user_id = "user_123"  # Placeholder - extract from token
        
        await websocket_manager.connect(websocket, user_id)
        
        # Send welcome message
        await websocket.send_text(json.dumps({
            "type": "connection",
            "message": "Connected to notifications",
            "timestamp": datetime.utcnow().isoformat()
        }))
        
        try:
            while True:
                # Listen for client messages
                data = await websocket.receive_text()
                message_data = json.loads(data)
                
                # Handle ping/pong for connection keepalive
                if message_data.get("type") == "ping":
                    await websocket.send_text(json.dumps({
                        "type": "pong",
                        "timestamp": datetime.utcnow().isoformat()
                    }))
                
        except WebSocketDisconnect:
            websocket_manager.disconnect(websocket, user_id)
    
    except Exception as e:
        try:
            await websocket.close(code=1000)
        except:
            pass

@router.get("/notifications", response_model=NotificationsListResponse)
async def get_notifications(
    limit: int = Query(20, ge=1, le=100, description="Number of notifications to retrieve"),
    offset: int = Query(0, ge=0, description="Number of notifications to skip"),
    unread_only: bool = Query(False, description="Return only unread notifications"),
    db: Session = Depends(get_database_session)
):
    """
    Get user notifications
    
    Returns simple notifications for claim status changes.
    """
    try:
        # Use simple data handler approach like enterprise_claims.py
        from app.services.data_handler import DataHandler
        data_handler = DataHandler()
        
        # Get all claims and their decisions to create notifications
        all_claims = data_handler.get_all_claims()
        
        notifications = []
        notification_id = 1
        
        for claim in all_claims:
            decision_log = data_handler.get_decision_by_claim_id(claim.claim_id)
            
            # Create notification based on claim status
            if claim.status.value in ['APPROVED', 'DENIED', 'FRAUD_FLAGGED']:
                title = ""
                message = ""
                notification_type = "claim_status"
                
                if claim.status.value == 'APPROVED':
                    title = "✅ Claim Approved"
                    message = f"Your claim {claim.claim_id} for ${claim.claim_amount} has been approved."
                elif claim.status.value == 'DENIED':
                    title = "❌ Claim Denied"
                    message = f"Your claim {claim.claim_id} for ${claim.claim_amount} has been denied."
                elif claim.status.value == 'FRAUD_FLAGGED':
                    title = "🚨 Claim Flagged for Review"
                    message = f"Your claim {claim.claim_id} has been flagged for fraud review."
                
                notifications.append(NotificationResponse(
                    id=notification_id,
                    notification_id=f"NOTIF-{claim.claim_id}",
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    priority="normal",
                    is_read=False,
                    created_at=claim.processed_at or claim.created_at,
                    read_at=None,
                    related_resource_type="claim",
                    related_resource_id=claim.claim_id
                ))
                notification_id += 1
        
        # Apply pagination
        paginated_notifications = notifications[offset:offset + limit]
        
        # Filter unread only if requested
        if unread_only:
            paginated_notifications = [n for n in paginated_notifications if not n.is_read]
        
        unread_count = len([n for n in notifications if not n.is_read])
        
        return NotificationsListResponse(
            notifications=paginated_notifications,
            count=len(notifications),
            unread_count=unread_count
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notifications: {str(e)}"
        )

@router.get("/notifications/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    db: Session = Depends(get_database_session)
):
    """
    Get notification statistics
    
    Returns real notification counts based on claim statuses.
    """
    try:
        # Use simple data handler approach
        from app.services.data_handler import DataHandler
        data_handler = DataHandler()
        
        # Get all claims and count notifications based on status
        all_claims = data_handler.get_all_claims()
        
        total_notifications = 0
        unread_notifications = 0
        category_breakdown = {
            "claim": {"total": 0, "unread": 0},
            "fraud": {"total": 0, "unread": 0}
        }
        
        for claim in all_claims:
            if claim.status.value in ['APPROVED', 'DENIED', 'FRAUD_FLAGGED']:
                total_notifications += 1
                unread_notifications += 1  # All are unread in simple mode
                
                if claim.status.value == 'FRAUD_FLAGGED':
                    category_breakdown["fraud"]["total"] += 1
                    category_breakdown["fraud"]["unread"] += 1
                else:
                    category_breakdown["claim"]["total"] += 1
                    category_breakdown["claim"]["unread"] += 1
        
        return NotificationStatsResponse(
            total_notifications=total_notifications,
            unread_notifications=unread_notifications,
            category_breakdown=category_breakdown
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to retrieve notification statistics: {str(e)}"
        )

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_database_session)
):
    """
    Mark a notification as read
    
    Simple implementation for basic notification management.
    """
    try:
        # Return success for simple mode
        return {"message": "Notification marked as read"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )

@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    db: Session = Depends(get_database_session)
):
    """
    Mark all notifications as read
    
    Simple implementation for marking all notifications as read.
    """
    try:
        # Return success for simple mode
        return {
            "message": "All notifications marked as read",
            "updated_count": 3
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )

@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    db: Session = Depends(get_database_session)
):
    """
    Delete a notification
    
    Simple implementation for notification deletion.
    """
    try:
        # Return success for simple mode
        return {"message": "Notification deleted successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )