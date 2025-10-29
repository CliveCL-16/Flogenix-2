"""
Notification API endpoints and WebSocket handlers
"""

from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from app.core.database import get_db
from app.core.security import get_current_user, get_current_user_websocket
from app.models import UserInfo
from app.services.notification_service import (
    NotificationService,
    notification_manager,
    Notification,
    NotificationType,
    NotificationCategory,
    NotificationPriority
)

router = APIRouter()


@router.websocket("/ws/notifications")
async def websocket_notifications(
    websocket: WebSocket,
    token: str = Query(...),
    db: Session = Depends(get_db)
):
    """WebSocket endpoint for real-time notifications"""
    
    try:
        # Authenticate user from token
        user = await get_current_user_websocket(token, db)
        if not user:
            await websocket.close(code=4001, reason="Authentication failed")
            return
            
        # Connect to notification manager
        await notification_manager.connect(websocket, user)
        
        try:
            while True:
                # Keep connection alive and handle any incoming messages
                data = await websocket.receive_text()
                
                # Handle ping/pong for connection health
                if data == "ping":
                    await websocket.send_text("pong")
                    
        except WebSocketDisconnect:
            pass
        finally:
            await notification_manager.disconnect(websocket, user.user_id)
            
    except Exception as e:
        print(f"WebSocket error: {e}")
        await websocket.close(code=4000, reason="Internal server error")


@router.get("/notifications")
async def get_notifications(
    unread_only: bool = Query(False, description="Get only unread notifications"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of notifications"),
    offset: int = Query(0, ge=0, description="Offset for pagination"),
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notifications for the current user"""
    
    service = NotificationService(db)
    notifications = service.get_user_notifications(
        user_id=current_user.user_id,
        unread_only=unread_only,
        limit=limit,
        offset=offset
    )
    
    return {
        "notifications": [
            {
                "id": n.id,
                "type": n.type,
                "category": n.category,
                "title": n.title,
                "message": n.message,
                "priority": n.priority,
                "read": n.read,
                "created_at": n.created_at,
                "action_url": n.action_url,
                "action_label": n.action_label,
                "related_entity_id": n.related_entity_id,
                "related_entity_type": n.related_entity_type
            }
            for n in notifications
        ],
        "count": len(notifications),
        "unread_count": len([n for n in notifications if not n.read])
    }


@router.post("/notifications/{notification_id}/read")
async def mark_notification_read(
    notification_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark a specific notification as read"""
    
    service = NotificationService(db)
    success = service.mark_as_read(notification_id, current_user.user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    return {"message": "Notification marked as read"}


@router.post("/notifications/read-all")
async def mark_all_notifications_read(
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Mark all notifications as read for the current user"""
    
    service = NotificationService(db)
    updated_count = service.mark_all_as_read(current_user.user_id)
    
    return {
        "message": f"Marked {updated_count} notifications as read",
        "updated_count": updated_count
    }


@router.delete("/notifications/{notification_id}")
async def delete_notification(
    notification_id: str,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Delete a notification (mark as read)"""
    
    service = NotificationService(db)
    success = service.delete_notification(notification_id, current_user.user_id)
    
    if not success:
        raise HTTPException(status_code=404, detail="Notification not found")
        
    return {"message": "Notification deleted"}


@router.get("/notifications/stats")
async def get_notification_stats(
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get notification statistics for the current user"""
    
    service = NotificationService(db)
    
    all_notifications = service.get_user_notifications(
        user_id=current_user.user_id,
        limit=1000  # Get more for stats
    )
    
    unread_count = len([n for n in all_notifications if not n.read])
    
    # Count by category
    category_counts = {}
    for notification in all_notifications:
        category = notification.category
        if category not in category_counts:
            category_counts[category] = {"total": 0, "unread": 0}
        category_counts[category]["total"] += 1
        if not notification.read:
            category_counts[category]["unread"] += 1
    
    # Count by priority
    priority_counts = {}
    for notification in all_notifications:
        priority = notification.priority
        if priority not in priority_counts:
            priority_counts[priority] = {"total": 0, "unread": 0}
        priority_counts[priority]["total"] += 1
        if not notification.read:
            priority_counts[priority]["unread"] += 1
    
    return {
        "total_notifications": len(all_notifications),
        "unread_notifications": unread_count,
        "read_notifications": len(all_notifications) - unread_count,
        "category_breakdown": category_counts,
        "priority_breakdown": priority_counts
    }


# Admin-only endpoints
@router.post("/admin/notifications/broadcast")
async def broadcast_notification(
    notification_data: dict,
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Broadcast a system notification to all users (admin only)"""
    
    if current_user.role not in ['ADMIN', 'SUPER_ADMIN']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    service = NotificationService(db)
    
    title = notification_data.get("title", "System Notification")
    message = notification_data.get("message", "")
    priority = notification_data.get("priority", NotificationPriority.LOW.value)
    
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    try:
        priority_enum = NotificationPriority(priority)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid priority")
    
    notification = await service.send_notification(
        title=title,
        message=message,
        type=NotificationType.SYSTEM,
        category=NotificationCategory.SYSTEM,
        priority=priority_enum,
        broadcast=True
    )
    
    return {
        "message": "Notification broadcast successfully",
        "notification_id": notification.id
    }


@router.get("/admin/notifications/system-stats")
async def get_system_notification_stats(
    current_user: UserInfo = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get system-wide notification statistics (admin only)"""
    
    if current_user.role not in ['ADMIN', 'SUPER_ADMIN']:
        raise HTTPException(status_code=403, detail="Admin access required")
    
    # Get all notifications in the system
    all_notifications = db.query(Notification).order_by(
        Notification.created_at.desc()
    ).limit(1000).all()
    
    total_notifications = len(all_notifications)
    system_notifications = len([n for n in all_notifications if n.user_id is None])
    user_notifications = total_notifications - system_notifications
    
    # Recent activity (last 24 hours)
    from datetime import datetime, timedelta, timezone
    recent_cutoff = datetime.now(timezone.utc) - timedelta(hours=24)
    recent_notifications = [n for n in all_notifications if n.created_at >= recent_cutoff]
    
    # Category breakdown
    category_stats = {}
    for notification in all_notifications[:100]:  # Last 100 for performance
        category = notification.category
        if category not in category_stats:
            category_stats[category] = 0
        category_stats[category] += 1
    
    return {
        "total_notifications": total_notifications,
        "system_notifications": system_notifications,
        "user_notifications": user_notifications,
        "recent_notifications_24h": len(recent_notifications),
        "active_connections": len(notification_manager.active_connections),
        "admin_connections": len(notification_manager.admin_connections),
        "category_distribution": category_stats
    }