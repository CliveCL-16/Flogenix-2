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
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Get user notifications
    
    Returns paginated list of notifications for the current user.
    """
    try:
        service = SimpleNotificationService(db)
        notifications = service.get_user_notifications(
            user_id=current_user.user_id,
            limit=limit,
            offset=offset,
            unread_only=unread_only
        )
        
        # Get counts
        all_notifications = service.get_user_notifications(current_user.user_id, limit=1000)
        unread_notifications = service.get_user_notifications(current_user.user_id, limit=1000, unread_only=True)
        
        notification_responses = []
        for notification in notifications:
            notification_responses.append(NotificationResponse(
                id=notification.id,
                notification_id=notification.notification_id,
                title=notification.title,
                message=notification.message,
                notification_type=notification.notification_type,
                priority=notification.priority,
                is_read=notification.is_read,
                created_at=notification.created_at,
                read_at=notification.read_at,
                related_resource_type=notification.related_resource_type,
                related_resource_id=notification.related_resource_id
            ))
        
        return NotificationsListResponse(
            notifications=notification_responses,
            count=len(all_notifications),
            unread_count=len(unread_notifications)
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notifications"
        )

@router.get("/notifications/stats", response_model=NotificationStatsResponse)
async def get_notification_stats(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Get notification statistics
    
    Returns notification counts and breakdown for the current user.
    """
    try:
        service = SimpleNotificationService(db)
        stats = service.get_notification_stats(current_user.user_id)
        
        return NotificationStatsResponse(**stats)
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve notification statistics"
        )

@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Mark a notification as read
    
    Marks the specified notification as read for the current user.
    """
    try:
        service = SimpleNotificationService(db)
        success = service.mark_as_read(notification_id, current_user.user_id)
        
        if success:
            return {"message": "Notification marked as read"}
        else:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notification as read"
        )

@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Mark all notifications as read
    
    Marks all unread notifications as read for the current user.
    """
    try:
        service = SimpleNotificationService(db)
        updated_count = service.mark_all_as_read(current_user.user_id)
        
        return {
            "message": f"Marked {updated_count} notifications as read",
            "updated_count": updated_count
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to mark notifications as read"
        )

@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Delete a notification
    
    Deletes the specified notification for the current user.
    """
    try:
        # Find user by user_id string
        user = db.query(User).filter(User.user_id == current_user.user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        notification = db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user.id
        ).first()
        
        if not notification:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Notification not found"
            )
        
        db.delete(notification)
        db.commit()
        
        return {"message": "Notification deleted successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to delete notification"
        )