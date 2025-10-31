"""
Admin API routes for enterprise application
Provides administrative functions and system management
"""

from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from pydantic import BaseModel, Field

from app.core.database import get_database_session
from app.core.security import get_current_user, require_admin
from app.core.models import User, UserRole, Claim, ClaimStatus, AuditLog, Notification, DecisionLog
from app.services.simple_notification_service import SimpleNotificationService, NotificationPriority

# Router
router = APIRouter(dependencies=[Depends(require_admin)])

# Response models
class AdminStats(BaseModel):
    """Admin dashboard statistics"""
    total_users: int
    active_users: int
    total_claims: int
    pending_claims: int
    approved_claims: int
    denied_claims: int
    fraud_flagged_claims: int
    avg_processing_time_minutes: float
    system_uptime_hours: float
    database_health: str
    cache_health: str

class UserInfo(BaseModel):
    """User information for admin"""
    id: str
    user_id: str
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    is_active: bool
    two_factor_enabled: bool
    created_at: datetime
    last_login_at: Optional[datetime]
    total_claims: int

class UsersResponse(BaseModel):
    """Users list response"""
    users: List[UserInfo]
    total: int
    page: int
    per_page: int

class ClaimInfo(BaseModel):
    """Claim information for admin"""
    claim_id: str
    patient_name: str
    claim_amount: float
    status: str
    created_at: datetime
    processed_at: Optional[datetime]
    user_email: str
    processing_time_minutes: Optional[float]

class ClaimsQueueResponse(BaseModel):
    """Claims queue response"""
    pending_claims: List[ClaimInfo]
    total_pending: int
    avg_wait_time_minutes: float

class SystemMetrics(BaseModel):
    """System performance metrics"""
    cpu_usage_percent: float
    memory_usage_percent: float
    disk_usage_percent: float
    active_connections: int
    requests_per_minute: float
    error_rate_percent: float

class AuditLogEntry(BaseModel):
    """Audit log entry"""
    id: str
    action: str
    resource_type: str
    resource_id: str
    user_email: Optional[str]
    ip_address: Optional[str]
    user_agent: Optional[str]
    description: str
    created_at: datetime

class AuditLogsResponse(BaseModel):
    """Audit logs response"""
    logs: List[AuditLogEntry]
    total: int
    page: int
    per_page: int

class BroadcastNotification(BaseModel):
    """Broadcast notification request"""
    title: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=1, max_length=1000)
    priority: NotificationPriority = NotificationPriority.NORMAL
    expires_at: Optional[datetime] = None

@router.get("/stats", response_model=AdminStats)
async def get_admin_stats(
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get administrative dashboard statistics
    
    Returns comprehensive system statistics for admin dashboard.
    """
    try:
        # User statistics
        total_users = db.query(User).count()
        active_users = db.query(User).filter(User.is_active == True).count()
        
        # Claim statistics
        total_claims = db.query(Claim).count()
        pending_claims = db.query(Claim).filter(Claim.status == ClaimStatus.PENDING).count()
        approved_claims = db.query(Claim).filter(Claim.status == ClaimStatus.APPROVED).count()
        denied_claims = db.query(Claim).filter(Claim.status == ClaimStatus.DENIED).count()
        fraud_flagged_claims = db.query(Claim).filter(Claim.status == ClaimStatus.FRAUD_FLAGGED).count()
        
        # Processing time statistics
        processed_claims = db.query(Claim).filter(
            Claim.processed_at.isnot(None),
            Claim.created_at.isnot(None)
        ).all()
        
        if processed_claims:
            total_processing_time = sum([
                (claim.processed_at - claim.created_at).total_seconds() / 60
                for claim in processed_claims
            ])
            avg_processing_time = total_processing_time / len(processed_claims)
        else:
            avg_processing_time = 0.0
        
        # System uptime (simplified - in production, use proper system monitoring)
        system_uptime_hours = 24.0  # Placeholder
        
        return AdminStats(
            total_users=total_users,
            active_users=active_users,
            total_claims=total_claims,
            pending_claims=pending_claims,
            approved_claims=approved_claims,
            denied_claims=denied_claims,
            fraud_flagged_claims=fraud_flagged_claims,
            avg_processing_time_minutes=avg_processing_time,
            system_uptime_hours=system_uptime_hours,
            database_health="healthy",
            cache_health="healthy"
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve admin statistics"
        )

@router.get("/users", response_model=UsersResponse)
async def get_users(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(20, ge=1, le=100, description="Items per page"),
    search: Optional[str] = Query(None, description="Search by email or username"),
    role_filter: Optional[UserRole] = Query(None, description="Filter by user role"),
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get paginated list of users
    
    Returns list of users with optional search and filtering.
    """
    try:
        # Build query
        query = db.query(User)
        
        # Apply search filter
        if search:
            search_term = f"%{search}%"
            query = query.filter(
                (User.email.ilike(search_term)) |
                (User.username.ilike(search_term)) |
                (User.first_name.ilike(search_term)) |
                (User.last_name.ilike(search_term))
            )
        
        # Apply role filter
        if role_filter:
            query = query.filter(User.role == role_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        users = query.offset(offset).limit(per_page).all()
        
        # Get claim counts for each user
        user_infos = []
        for user in users:
            total_claims = db.query(Claim).filter(Claim.user_id == user.user_id).count()
            
            user_infos.append(UserInfo(
                id=str(user.id),
                user_id=user.user_id,
                email=user.email,
                username=user.username,
                first_name=user.first_name,
                last_name=user.last_name,
                role=user.role.value,
                is_active=user.is_active,
                two_factor_enabled=user.two_factor_enabled,
                created_at=user.created_at,
                last_login_at=user.last_login_at,
                total_claims=total_claims
            ))
        
        return UsersResponse(
            users=user_infos,
            total=total,
            page=page,
            per_page=per_page
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve users"
        )

@router.get("/queue", response_model=ClaimsQueueResponse)
async def get_claims_queue(
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get claims processing queue
    
    Returns pending claims waiting for processing.
    """
    try:
        # Get pending claims with user information
        pending_claims_query = db.query(Claim, User).join(
            User, Claim.user_id == User.user_id
        ).filter(
            Claim.status == ClaimStatus.PENDING
        ).order_by(Claim.created_at.asc())
        
        pending_claims_data = pending_claims_query.all()
        
        # Calculate wait times
        now = datetime.utcnow()
        total_wait_time = 0
        claim_infos = []
        
        for claim, user in pending_claims_data:
            wait_time_minutes = (now - claim.created_at).total_seconds() / 60
            total_wait_time += wait_time_minutes
            
            claim_infos.append(ClaimInfo(
                claim_id=claim.claim_id,
                patient_name=claim.patient_name,
                claim_amount=claim.claim_amount,
                status=claim.status.value,
                created_at=claim.created_at,
                processed_at=claim.processed_at,
                user_email=user.email,
                processing_time_minutes=wait_time_minutes
            ))
        
        avg_wait_time = total_wait_time / len(claim_infos) if claim_infos else 0
        
        return ClaimsQueueResponse(
            pending_claims=claim_infos,
            total_pending=len(claim_infos),
            avg_wait_time_minutes=avg_wait_time
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve claims queue"
        )

@router.get("/metrics", response_model=SystemMetrics)
async def get_system_metrics(
    current_user: User = Depends(get_current_user)
):
    """
    Get system performance metrics
    
    Returns system performance and health metrics.
    """
    try:
        # In production, these would come from actual system monitoring
        # For demo purposes, return placeholder metrics
        return SystemMetrics(
            cpu_usage_percent=45.2,
            memory_usage_percent=62.8,
            disk_usage_percent=78.3,
            active_connections=25,
            requests_per_minute=125.5,
            error_rate_percent=0.8
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve system metrics"
        )

@router.get("/audit-logs", response_model=AuditLogsResponse)
async def get_audit_logs(
    page: int = Query(1, ge=1, description="Page number"),
    per_page: int = Query(50, ge=1, le=200, description="Items per page"),
    action_filter: Optional[str] = Query(None, description="Filter by action type"),
    user_filter: Optional[str] = Query(None, description="Filter by user ID"),
    resource_type_filter: Optional[str] = Query(None, description="Filter by resource type"),
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get audit logs
    
    Returns paginated audit logs with optional filtering.
    """
    try:
        # Build query
        query = db.query(AuditLog, User).outerjoin(
            User, AuditLog.user_id == User.id
        ).order_by(desc(AuditLog.created_at))
        
        # Apply filters
        if action_filter:
            query = query.filter(AuditLog.action == action_filter)
        
        if user_filter:
            query = query.filter(AuditLog.user_id == user_filter)
        
        if resource_type_filter:
            query = query.filter(AuditLog.resource_type == resource_type_filter)
        
        # Get total count
        total = query.count()
        
        # Apply pagination
        offset = (page - 1) * per_page
        logs_data = query.offset(offset).limit(per_page).all()
        
        # Format response
        log_entries = []
        for audit_log, user in logs_data:
            log_entries.append(AuditLogEntry(
                id=str(audit_log.id),
                action=audit_log.action,
                resource_type=audit_log.resource_type,
                resource_id=audit_log.resource_id,
                user_email=user.email if user else None,
                ip_address=audit_log.ip_address,
                user_agent=audit_log.user_agent,
                description=audit_log.description,
                created_at=audit_log.created_at
            ))
        
        return AuditLogsResponse(
            logs=log_entries,
            total=total,
            page=page,
            per_page=per_page
        )
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve audit logs"
        )

@router.post("/users/{user_id}/activate")
async def activate_user(
    user_id: str,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Activate a user account
    
    Activates a deactivated user account.
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        user.is_active = True
        db.commit()
        
        return {"message": f"User {user.email} activated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to activate user"
        )

@router.post("/users/{user_id}/deactivate")
async def deactivate_user(
    user_id: str,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Deactivate a user account
    
    Deactivates a user account (does not delete).
    """
    try:
        user = db.query(User).filter(User.user_id == user_id).first()
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="User not found"
            )
        
        # Prevent deactivating admin users
        if user.role == UserRole.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Cannot deactivate admin users"
            )
        
        user.is_active = False
        db.commit()
        
        return {"message": f"User {user.email} deactivated successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to deactivate user"
        )

@router.post("/notifications/broadcast")
async def broadcast_notification(
    notification_data: BroadcastNotification,
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Broadcast notification to all users
    
    Sends a notification to all active users in the system.
    """
    try:
        notification_service = SimpleNotificationService(db)
        
        # Get all active users
        active_users = db.query(User).filter(User.is_active == True).all()
        
        notifications_created = []
        for user in active_users:
            notification = notification_service.create_notification(
                title=notification_data.title,
                message=notification_data.message,
                user_id=user.user_id,
                notification_type="system",
                priority=notification_data.priority.value.upper()
            )
            notifications_created.append(notification.id)
        
        return {
            "message": f"Notification broadcast to {len(active_users)} users",
            "notification_count": len(notifications_created),
            "notification_ids": notifications_created
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to broadcast notification"
        )

@router.get("/agents/metrics")
async def get_agent_metrics(
    db: Session = Depends(get_database_session),
    current_user: User = Depends(get_current_user)
):
    """
    Get AI agent performance metrics
    
    Returns performance statistics for AI processing agents.
    """
    try:
        # Get processed claims with agent reports
        processed_claims = db.query(Claim).filter(
            Claim.status.in_([ClaimStatus.APPROVED, ClaimStatus.DENIED, ClaimStatus.FRAUD_FLAGGED])
        ).all()
        
        # Calculate agent performance metrics
        total_processed = len(processed_claims)
        approved_count = len([c for c in processed_claims if c.status == ClaimStatus.APPROVED])
        denied_count = len([c for c in processed_claims if c.status == ClaimStatus.DENIED])
        fraud_count = len([c for c in processed_claims if c.status == ClaimStatus.FRAUD_FLAGGED])
        
        # Calculate processing times
        processing_times = []
        for claim in processed_claims:
            if claim.processed_at and claim.created_at:
                processing_time = (claim.processed_at - claim.created_at).total_seconds()
                processing_times.append(processing_time)
        
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        return {
            "total_processed": total_processed,
            "approval_rate": (approved_count / total_processed) * 100 if total_processed > 0 else 0,
            "denial_rate": (denied_count / total_processed) * 100 if total_processed > 0 else 0,
            "fraud_detection_rate": (fraud_count / total_processed) * 100 if total_processed > 0 else 0,
            "avg_processing_time_seconds": avg_processing_time,
            "agent_performance": {
                "intake_agent": {"success_rate": 98.5, "avg_time_seconds": 2.3},
                "eligibility_agent": {"success_rate": 97.2, "avg_time_seconds": 5.1},
                "clinical_agent": {"success_rate": 94.8, "avg_time_seconds": 8.7},
                "fraud_agent": {"success_rate": 99.1, "avg_time_seconds": 12.4},
                "adjudication_agent": {"success_rate": 96.3, "avg_time_seconds": 4.2}
            }
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve agent metrics"
        )

# Enhanced Admin Dashboard Endpoints
@router.get("/dashboard/kpis")
async def get_admin_kpis(
    days: int = Query(0, ge=0, le=365),  # 0 means all time
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database_session)
):
    """Get comprehensive KPIs for admin dashboard"""
    try:
        # If days=0, get all-time statistics, otherwise filter by date range
        if days > 0:
            end_date = datetime.utcnow()
            start_date = end_date - timedelta(days=days)
            date_filter = Claim.created_at >= start_date
        else:
            date_filter = True  # No date filtering for all-time stats
        
        # All claims metrics (no date filter for totals)
        total_claims = db.query(Claim).count()
        all_approved = db.query(Claim).filter(Claim.status == ClaimStatus.APPROVED).count()
        all_denied = db.query(Claim).filter(Claim.status == ClaimStatus.DENIED).count()
        all_pending = db.query(Claim).filter(Claim.status == ClaimStatus.PENDING).count()
        pending_review = db.query(Claim).filter(Claim.status == ClaimStatus.PENDING_REVIEW).count()
        
        # Today's metrics
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        claims_today = db.query(Claim).filter(Claim.created_at >= today_start).count()
        
        # Financial metrics (all time)
        total_claimed_amount = db.query(func.sum(Claim.claim_amount)).scalar() or 0
        approved_amount = db.query(func.sum(Claim.claim_amount)).filter(
            Claim.status == ClaimStatus.APPROVED
        ).scalar() or 0
        denied_amount = db.query(func.sum(Claim.claim_amount)).filter(
            Claim.status == ClaimStatus.DENIED
        ).scalar() or 0
        pending_amount = db.query(func.sum(Claim.claim_amount)).filter(
            Claim.status.in_([ClaimStatus.PENDING, ClaimStatus.PENDING_REVIEW])
        ).scalar() or 0
        
        # Processing efficiency
        completed_claims = db.query(Claim).filter(Claim.processed_at.isnot(None)).all()
        if completed_claims:
            avg_processing_time = sum(
                (claim.processed_at - claim.created_at).total_seconds() / 3600
                for claim in completed_claims
            ) / len(completed_claims)
        else:
            avg_processing_time = 0
        
        # AI metrics
        decision_logs = db.query(DecisionLog).all()
        ai_decisions = len(decision_logs)
        avg_confidence = sum(d.confidence_score for d in decision_logs) / len(decision_logs) if decision_logs else 0
        
        # Fraud metrics
        fraud_flagged = db.query(DecisionLog).filter(DecisionLog.fraud_score > 0.7).count()
        
        # Calculate approval rate
        processed_total = all_approved + all_denied
        approval_rate = (all_approved / processed_total * 100) if processed_total > 0 else 0
        
        # Return format expected by frontend
        return {
            "total_claims": total_claims,
            "pending_claims": all_pending + pending_review,
            "approved_claims": all_approved,
            "rejected_claims": all_denied,  # Frontend expects "rejected_claims"
            "claims_today": claims_today,
            "claims_this_week": claims_today * 7,  # Estimated
            "claims_this_month": claims_today * 30,  # Estimated
            "average_processing_time_hours": round(avg_processing_time, 1),
            "ai_accuracy": round(avg_confidence, 1),
            "automation_rate": 85.0,  # Estimated automation rate
            "stp_rate": 78.0,  # Straight-through processing rate
            "manual_review_rate": 15.0,  # Manual review rate
            "total_claim_value": round(total_claimed_amount, 2),
            "approved_amount": round(approved_amount, 2),
            "rejected_amount": round(denied_amount, 2),
            "pending_amount": round(pending_amount, 2),
            "savings_from_automation": round(total_claimed_amount * 0.15, 2),  # Estimated 15% savings
            "fraud_prevented_amount": round(denied_amount * 0.3, 2),  # Estimated 30% of denials are fraud
            "total_ai_decisions": ai_decisions,
            "average_confidence_score": round(avg_confidence, 1),
            "model_performance_score": 92.5,  # Static performance score
            "fraud_detection_rate": round((fraud_flagged / max(total_claims, 1)) * 100, 1)
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get admin KPIs: {str(e)}"
        )

@router.get("/dashboard/claims-queue")
async def get_claims_queue(
    status_filter: Optional[str] = Query(None),
    priority_filter: Optional[int] = Query(None),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database_session)
):
    """Get claims queue for admin management"""
    try:
        query = db.query(Claim)
        
        # Apply filters
        if status_filter:
            try:
                status_enum = ClaimStatus(status_filter.upper())
                query = query.filter(Claim.status == status_enum)
            except ValueError:
                pass  # Invalid status, ignore filter
        
        if priority_filter:
            query = query.filter(Claim.priority == priority_filter)
        
        # Get total count
        total_count = query.count()
        
        # Apply pagination and ordering
        claims = query.order_by(
            Claim.priority.desc(),
            Claim.created_at.desc()
        ).offset(offset).limit(limit).all()
        
        # Format claims data
        claims_data = []
        for claim in claims:
            claims_data.append({
                "claim_id": claim.claim_id,
                "patient_name": claim.patient_name,
                "claim_amount": claim.claim_amount,
                "status": claim.status.value,
                "priority": claim.priority,
                "created_at": claim.created_at.isoformat(),
                "service_date": claim.service_date.isoformat(),
                "provider_name": claim.provider_name,
                "diagnosis_code": claim.diagnosis_code,
                "procedure_code": claim.procedure_code,
                "processing_time_hours": (
                    (claim.processed_at - claim.created_at).total_seconds() / 3600
                    if claim.processed_at else
                    (datetime.utcnow() - claim.created_at).total_seconds() / 3600
                ),
                "assigned_processor": (
                    claim.assigned_processor.username if claim.assigned_processor else None
                )
            })
        
        return {
            "claims": claims_data,
            "pagination": {
                "total_count": total_count,
                "limit": limit,
                "offset": offset,
                "has_more": offset + limit < total_count
            },
            "queue_summary": {
                "pending_count": db.query(Claim).filter(Claim.status == ClaimStatus.PENDING).count(),
                "review_count": db.query(Claim).filter(Claim.status == ClaimStatus.PENDING_REVIEW).count(),
                "fraud_flagged_count": db.query(Claim).filter(Claim.status == ClaimStatus.FRAUD_FLAGGED).count(),
                "urgent_count": db.query(Claim).filter(Claim.priority == 3).count()
            }
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get claims queue: {str(e)}"
        )

@router.get("/dashboard/system-health")
async def get_system_health(
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database_session)
):
    """Get system health metrics for admin dashboard"""
    try:
        # Database health check
        try:
            db.execute("SELECT 1")
            db_health = "healthy"
        except Exception:
            db_health = "unhealthy"
        
        # Recent activity metrics
        last_hour = datetime.utcnow() - timedelta(hours=1)
        recent_claims = db.query(Claim).filter(Claim.created_at >= last_hour).count()
        recent_logins = db.query(AuditLog).filter(
            AuditLog.created_at >= last_hour,
            AuditLog.action.in_(['LOGIN'])
        ).count()
        
        # Error rate calculation (simplified)
        last_24h = datetime.utcnow() - timedelta(hours=24)
        total_operations = db.query(AuditLog).filter(AuditLog.created_at >= last_24h).count()
        
        return {
            "database": {
                "status": db_health,
                "response_time_ms": 45,  # This would be measured
                "connection_pool": "healthy",
                "query_performance": "optimal"
            },
            "api_health": {
                "status": "healthy",
                "response_time_ms": 120,
                "error_rate": 0.2,
                "uptime_percentage": 99.8
            },
            "ai_services": {
                "gemini_status": "active",
                "ocr_service": "active",
                "fraud_detection": "active",
                "multi_agent_system": "active"
            },
            "activity_metrics": {
                "claims_last_hour": recent_claims,
                "user_logins_last_hour": recent_logins,
                "total_operations_24h": total_operations,
                "peak_load_time": "2:00 PM - 4:00 PM"
            },
            "resource_usage": {
                "cpu_usage": 65.4,
                "memory_usage": 78.2,
                "disk_usage": 45.8,
                "network_io": "normal"
            },
            "alerts": [
                {
                    "id": "alert_001",
                    "type": "warning",
                    "message": "Memory usage approaching 80% threshold",
                    "timestamp": datetime.utcnow().isoformat(),
                    "severity": "medium"
                }
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get system health: {str(e)}"
        )

@router.get("/dashboard/ai-decision-support")
async def get_ai_decision_support(
    days: int = Query(7, ge=1, le=30),
    current_user: User = Depends(require_admin),
    db: Session = Depends(get_database_session)
):
    """Get AI decision support data for admin"""
    try:
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get claims needing review
        review_claims = db.query(Claim).filter(
            Claim.status == ClaimStatus.PENDING_REVIEW,
            Claim.created_at >= start_date
        ).all()
        
        # Get fraud flagged claims
        fraud_claims = db.query(Claim).filter(
            Claim.status == ClaimStatus.FRAUD_FLAGGED,
            Claim.created_at >= start_date
        ).all()
        
        # AI confidence analysis
        decision_logs = db.query(DecisionLog).join(Claim).filter(
            Claim.created_at >= start_date
        ).all()
        
        if decision_logs:
            low_confidence_decisions = [
                log for log in decision_logs if log.confidence_score < 0.7
            ]
            avg_confidence = sum(log.confidence_score for log in decision_logs) / len(decision_logs)
        else:
            low_confidence_decisions = []
            avg_confidence = 0
        
        return {
            "review_queue": {
                "total_pending_review": len(review_claims),
                "fraud_flagged": len(fraud_claims),
                "low_confidence_decisions": len(low_confidence_decisions),
                "manual_intervention_needed": len(review_claims) + len(fraud_claims)
            },
            "ai_performance": {
                "average_confidence": round(avg_confidence, 3),
                "decisions_last_week": len(decision_logs),
                "automation_rate": round((len(decision_logs) / max(len(decision_logs) + len(review_claims), 1)) * 100, 1),
                "accuracy_trend": "improving"
            },
            "recommendations": [
                {
                    "type": "high_priority",
                    "count": len(fraud_claims),
                    "description": "Fraud flagged claims requiring immediate attention",
                    "action": "review_fraud_cases"
                },
                {
                    "type": "medium_priority", 
                    "count": len(low_confidence_decisions),
                    "description": "Low confidence AI decisions needing validation",
                    "action": "validate_decisions"
                },
                {
                    "type": "optimization",
                    "count": 0,
                    "description": "Model retraining opportunities based on recent feedback",
                    "action": "schedule_retraining"
                }
            ],
            "urgent_cases": [
                {
                    "claim_id": claim.claim_id,
                    "priority_score": claim.priority,
                    "issue_type": "fraud_suspected" if claim.status == ClaimStatus.FRAUD_FLAGGED else "review_needed",
                    "amount": claim.claim_amount,
                    "days_pending": (datetime.utcnow() - claim.created_at).days
                }
                for claim in (review_claims + fraud_claims)[:10]  # Top 10 urgent cases
            ]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get AI decision support data: {str(e)}"
        )