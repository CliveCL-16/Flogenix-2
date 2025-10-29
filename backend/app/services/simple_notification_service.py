"""
Simple notification service that works with existing models
"""

import asyncio
import json
from datetime import datetime
from typing import Dict, List, Optional, Set
from enum import Enum

from fastapi import WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session
from sqlalchemy import desc

from app.core.models import Notification, User


class NotificationType(str, Enum):
    INFO = "info"
    SUCCESS = "success" 
    WARNING = "warning"
    ERROR = "error"
    SYSTEM = "system"


class NotificationPriority(str, Enum):
    LOW = "LOW"
    NORMAL = "NORMAL"
    HIGH = "HIGH"
    URGENT = "URGENT"


class NotificationCategory(str, Enum):
    CLAIM = "claim"
    FRAUD = "fraud"
    SYSTEM = "system"
    USER = "user"


class SimpleNotificationService:
    """Simple notification service using existing models"""
    
    def __init__(self, db: Session):
        self.db = db
    
    def create_notification(
        self,
        title: str,
        message: str,
        user_id: str,
        notification_type: str = "system",
        priority: str = "NORMAL",
        related_resource_type: Optional[str] = None,
        related_resource_id: Optional[str] = None
    ) -> Notification:
        """Create a new notification"""
        
        # Find user by user_id (string) and get actual database ID
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise ValueError(f"User with user_id {user_id} not found")
        
        notification = Notification(
            user_id=user.id,  # Use the actual database ID
            title=title,
            message=message,
            notification_type=notification_type,
            priority=priority,
            related_resource_type=related_resource_type,
            related_resource_id=related_resource_id,
            is_read=False,
            created_at=datetime.utcnow()
        )
        
        self.db.add(notification)
        self.db.commit()
        self.db.refresh(notification)
        
        return notification
    
    def get_user_notifications(
        self,
        user_id: str,
        limit: int = 50,
        offset: int = 0,
        unread_only: bool = False
    ) -> List[Notification]:
        """Get notifications for a user"""
        
        # Find user by user_id string
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return []
        
        query = self.db.query(Notification).filter(
            Notification.user_id == user.id
        )
        
        if unread_only:
            query = query.filter(Notification.is_read == False)
        
        return query.order_by(desc(Notification.created_at)).offset(offset).limit(limit).all()
    
    def mark_as_read(self, notification_id: int, user_id: str) -> bool:
        """Mark a notification as read"""
        
        # Find user by user_id string
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return False
        
        notification = self.db.query(Notification).filter(
            Notification.id == notification_id,
            Notification.user_id == user.id
        ).first()
        
        if notification:
            notification.is_read = True
            notification.read_at = datetime.utcnow()
            self.db.commit()
            return True
        
        return False
    
    def mark_all_as_read(self, user_id: str) -> int:
        """Mark all notifications as read for a user"""
        
        # Find user by user_id string
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return 0
        
        count = self.db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.is_read == False
        ).update({
            'is_read': True,
            'read_at': datetime.utcnow()
        })
        
        self.db.commit()
        return count
    
    def get_notification_stats(self, user_id: str) -> dict:
        """Get notification statistics for a user"""
        
        # Find user by user_id string
        user = self.db.query(User).filter(User.user_id == user_id).first()
        if not user:
            return {
                "total_notifications": 0,
                "unread_notifications": 0,
                "category_breakdown": {}
            }
        
        total = self.db.query(Notification).filter(
            Notification.user_id == user.id
        ).count()
        
        unread = self.db.query(Notification).filter(
            Notification.user_id == user.id,
            Notification.is_read == False
        ).count()
        
        return {
            "total_notifications": total,
            "unread_notifications": unread,
            "category_breakdown": {
                "system": total  # Simplified for now
            }
        }


# WebSocket manager for real-time notifications
class WebSocketManager:
    """Simple WebSocket manager for real-time notifications"""
    
    def __init__(self):
        self.active_connections: Dict[str, Set[WebSocket]] = {}
    
    async def connect(self, websocket: WebSocket, user_id: str):
        """Connect a WebSocket for a user"""
        await websocket.accept()
        
        if user_id not in self.active_connections:
            self.active_connections[user_id] = set()
        
        self.active_connections[user_id].add(websocket)
    
    def disconnect(self, websocket: WebSocket, user_id: str):
        """Disconnect a WebSocket"""
        if user_id in self.active_connections:
            self.active_connections[user_id].discard(websocket)
            if not self.active_connections[user_id]:
                del self.active_connections[user_id]
    
    async def send_personal_message(self, message: str, user_id: str):
        """Send a message to a specific user"""
        if user_id in self.active_connections:
            disconnected = []
            for websocket in self.active_connections[user_id].copy():
                try:
                    await websocket.send_text(message)
                except:
                    disconnected.append(websocket)
            
            # Clean up disconnected websockets
            for ws in disconnected:
                self.active_connections[user_id].discard(ws)
    
    async def broadcast_message(self, message: str):
        """Broadcast a message to all connected users"""
        for user_id, connections in self.active_connections.items():
            for websocket in connections.copy():
                try:
                    await websocket.send_text(message)
                except:
                    connections.discard(websocket)


# Global WebSocket manager instance
websocket_manager = WebSocketManager()


# For compatibility with existing imports
NotificationService = SimpleNotificationService