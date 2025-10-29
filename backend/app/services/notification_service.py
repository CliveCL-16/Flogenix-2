"""
Real-time notification system for enterprise platform
Handles WebSocket connections, notification broadcasting, and persistence
"""

import asyncio
import json
import uuid
from datetime import datetime, timezone
from typing import Dict, List, Optional, Set
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import Column, String, DateTime, Boolean, Integer, Text

from app.core.database import get_database_session, Base
from app.core.security import get_current_user
from app.core.models import Notification, User


class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"


class NotificationCategory(str, Enum):
    CLAIM = "claim"
    FRAUD = "fraud"
    SYSTEM = "system"
    USER = "user"
    PERFORMANCE = "performance"


class NotificationPriority(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class NotificationManager:
    def __init__(self):
        # Active WebSocket connections by user_id
        self.active_connections: Dict[str, Set[WebSocket]] = {}
        # Admin connections (users with admin privileges)
        self.admin_connections: Set[WebSocket] = set()
        
    async def connect(self, websocket: WebSocket, user: User):
        """Connect a WebSocket for a specific user"""
        await websocket.accept()
        
        user_id = user.user_id
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
        
        # Add to admin connections if user has admin privileges
        if user.role in ['ADMIN', 'SUPER_ADMIN']:
            self.admin_connections.add(websocket)
            
        print(f"✅ WebSocket connected for user {user.username} ({user_id})")
        
    async def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
                
        self.admin_connections.discard(websocket)
        print(f"❌ WebSocket disconnected for user {user_id}")
        
    async def send_to_user(self, user_id: str, notification: dict):
        """Send notification to specific user"""
        if user_id in self.active_connections:
            disconnected = set()
            
            for websocket in self.active_connections[user_id]:
                try:
                    await websocket.send_text(json.dumps(notification))
                except Exception as e:
                    print(f"Error sending to user {user_id}: {e}")
                    disconnected.add(websocket)
                    
            # Remove disconnected WebSockets
            for ws in disconnected:
                self.active_connections[user_id].discard(ws)
                
    async def send_to_admins(self, notification: dict):
        """Send notification to all admin users"""
        disconnected = set()
        
        for websocket in self.admin_connections:
            try:
                await websocket.send_text(json.dumps(notification))
            except Exception as e:
                print(f"Error sending to admin: {e}")
                disconnected.add(websocket)
                
        # Remove disconnected WebSockets
        for ws in disconnected:
            self.admin_connections.discard(ws)
            
    async def broadcast_system(self, notification: dict):
        """Broadcast system notification to all connected users"""
        all_websockets = set()
        for user_connections in self.active_connections.values():
            all_websockets.update(user_connections)
            
        disconnected = set()
        for websocket in all_websockets:
            try:
                await websocket.send_text(json.dumps(notification))
            except Exception as e:
                print(f"Error broadcasting: {e}")
                disconnected.add(websocket)
                
        # Clean up disconnected WebSockets
        for user_id in list(self.active_connections.keys()):
            self.active_connections[user_id] -= disconnected
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]


# Global notification manager instance
notification_manager = NotificationManager()


class NotificationService:
    def __init__(self, db: Session):
        self.db = db
        
    def create_notification(
        self,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        priority: NotificationPriority = NotificationPriority.LOW,
        user_id: Optional[str] = None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        related_entity_id: Optional[str] = None,
        related_entity_type: Optional[str] = None
    ) -> Notification:
        """Create and persist a notification"""
        
        notification = Notification(
            user_id=user_id,
            type=type.value,
            category=category.value,
            title=title,
            message=message,
            priority=priority.value,
            action_url=action_url,
            action_label=action_label,
            related_entity_id=related_entity_id,
            related_entity_type=related_entity_type
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        return notification
        
    async def send_notification(
        self,
        title: str,
        message: str,
        type: NotificationType = NotificationType.INFO,
        category: NotificationCategory = NotificationCategory.SYSTEM,
        priority: NotificationPriority = NotificationPriority.LOW,
        user_id: Optional[str] = None,
        action_url: Optional[str] = None,
        action_label: Optional[str] = None,
        related_entity_id: Optional[str] = None,
        related_entity_type: Optional[str] = None,
        send_to_admins: bool = False,
        broadcast: bool = False
    ):
        """Create notification and send via WebSocket"""
        
        # Create and persist notification
        notification = self.create_notification(
            title=title,
            message=message,
            type=type,
            category=category,
            priority=priority,
            user_id=user_id,
            action_url=action_url,
            action_label=action_label,
            related_entity_id=related_entity_id,
            related_entity_type=related_entity_type
        )
        
        # Format for WebSocket transmission
        notification_dict = {
            "id": notification.id,
            "type": notification.type,
            "category": notification.category,
            "title": notification.title,
            "message": notification.message,
            "priority": notification.priority,
            "read": notification.read,
            "created_at": notification.created_at.isoformat(),
            "action_url": notification.action_url,
            "action_label": notification.action_label,
            "related_entity_id": notification.related_entity_id,
            "related_entity_type": notification.related_entity_type
        }
        
        # Send via WebSocket based on targeting
        if broadcast:
            await notification_manager.broadcast_system(notification_dict)
        elif send_to_admins:
            await notification_manager.send_to_admins(notification_dict)
        elif user_id:
            await notification_manager.send_to_user(user_id, notification_dict)
            
        return notification
        
    def get_user_notifications(
        self,
        user_id: str,
        unread_only: bool = False,
        limit: int = 50,
        offset: int = 0
    ) -> List[Notification]:
        """Get notifications for a specific user"""
        
        query = self.db.query(Notification).filter(
            (Notification.user_id == user_id) | (Notification.user_id.is_(None))
        )
        
        if unread_only:
            query = query.filter(Notification.read == False)
            
        notifications = query.order_by(
            Notification.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        return notifications
        
    def mark_as_read(self, notification_id: str, user_id: str) -> bool:
        """Mark notification as read"""
        
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            (Notification.user_id == user_id) | (Notification.user_id.is_(None))
        ).first()
        
        if notification:
            notification.read = True
            self.db.commit()
            return True
            
        return False
        
    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        
        updated_count = self.db.query(Notification).filter(
            (Notification.user_id == user_id) | (Notification.user_id.is_(None)),
            Notification.read == False
        ).update({Notification.read: True})
        
        self.db.commit()
        return updated_count
        
    def delete_notification(self, notification_id: str, user_id: str) -> bool:
        """Delete a notification (soft delete by marking as read)"""
        
        return self.mark_as_read(notification_id, user_id)


# Utility functions for common notification scenarios

async def notify_claim_processed(
    db: Session,
    claim_id: str,
    user_id: str,
    status: str,
    amount: float = None
):
    """Send notification when a claim is processed"""
    
    service = NotificationService(db)
    
    if status.upper() == "APPROVED":
        title = "Claim Approved"
        message = f"Your claim {claim_id} has been approved"
        if amount:
            message += f" for ${amount:,.2f}"
        type = NotificationType.SUCCESS
    elif status.upper() == "DENIED":
        title = "Claim Denied"
        message = f"Your claim {claim_id} has been denied. Please review the details."
        type = NotificationType.WARNING
    else:
        title = "Claim Status Updated"
        message = f"Your claim {claim_id} status has been updated to {status}"
        type = NotificationType.INFO
        
    await service.send_notification(
        title=title,
        message=message,
        type=type,
        category=NotificationCategory.CLAIM,
        priority=NotificationPriority.MEDIUM,
        user_id=user_id,
        action_url=f"/enterprise/user/claim/{claim_id}",
        action_label="View Claim",
        related_entity_id=claim_id,
        related_entity_type="claim"
    )


async def notify_fraud_detected(
    db: Session,
    claim_id: str,
    risk_score: float,
    user_id: str = None
):
    """Send fraud detection notification"""
    
    service = NotificationService(db)
    
    await service.send_notification(
        title="High-Risk Claim Detected",
        message=f"Claim {claim_id} has been flagged for potential fraud with a risk score of {risk_score:.1f}%. Manual review required.",
        type=NotificationType.WARNING,
        category=NotificationCategory.FRAUD,
        priority=NotificationPriority.HIGH,
        user_id=user_id,
        action_url=f"/enterprise/admin/claim/{claim_id}",
        action_label="Review Claim",
        related_entity_id=claim_id,
        related_entity_type="claim",
        send_to_admins=True
    )


async def notify_system_event(
    db: Session,
    title: str,
    message: str,
    priority: NotificationPriority = NotificationPriority.LOW,
    broadcast: bool = True
):
    """Send system-wide notification"""
    
    service = NotificationService(db)
    
    await service.send_notification(
        title=title,
        message=message,
        type=NotificationType.SYSTEM,
        category=NotificationCategory.SYSTEM,
        priority=priority,
        broadcast=broadcast
    )


async def notify_user_action(
    db: Session,
    title: str,
    message: str,
    user_id: str,
    action_url: str = None,
    action_label: str = None
):
    """Send user-specific action notification"""
    
    service = NotificationService(db)
    
    await service.send_notification(
        title=title,
        message=message,
        type=NotificationType.INFO,
        category=NotificationCategory.USER,
        priority=NotificationPriority.LOW,
        user_id=user_id,
        action_url=action_url,
        action_label=action_label
    )