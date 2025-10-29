"""
Notification Tasks for Real-time Updates
Handles email, SMS, and in-app notifications for claim status changes
"""

from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from sqlalchemy.orm import Session
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import json

from app.core.celery_app import celery_app
from app.core.database import get_database_session
from app.core.models import User, Claim, Notification, ClaimStatus
from app.core.config import get_settings

settings = get_settings()

@celery_app.task
def send_claim_status_notification(claim_id: str, new_status: str, decision: Optional[str] = None, confidence_score: Optional[float] = None):
    """
    Send notification when claim status changes
    """
    try:
        db = next(get_database_session())
        
        # Get claim and user
        claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            return {"error": "Claim not found"}
        
        user = db.query(User).filter(User.id == claim.user_id).first()
        if not user:
            return {"error": "User not found"}
        
        # Create notification content based on status
        notification_content = _create_status_notification_content(
            claim, new_status, decision, confidence_score
        )
        
        # Create in-app notification
        notification = Notification(
            user_id=user.id,
            title=notification_content["title"],
            message=notification_content["message"],
            notification_type="claim_status_update",
            priority=notification_content["priority"],
            related_resource_type="claim",
            related_resource_id=claim_id,
            delivery_channels=["in_app", "email"]
        )
        
        db.add(notification)
        db.commit()
        
        # Send email notification
        email_sent = _send_email_notification(
            user.email,
            notification_content["title"],
            notification_content["email_body"],
            user.first_name
        )
        
        # Update notification delivery status
        if email_sent:
            notification.delivered_at = datetime.utcnow()
            db.commit()
        
        # Send to admin/processors if high priority
        if notification_content["priority"] in ["HIGH", "URGENT"]:
            _send_admin_notification.delay(claim_id, new_status, notification_content)
        
        return {
            "notification_id": notification.notification_id,
            "email_sent": email_sent,
            "delivery_channels": notification.delivery_channels
        }
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task
def _send_admin_notification(claim_id: str, status: str, content: Dict[str, Any]):
    """
    Send notification to admins and processors for high-priority claims
    """
    try:
        db = next(get_database_session())
        
        # Get admin and processor users
        admin_users = db.query(User).filter(
            User.role.in_(["ADMIN", "SUPER_ADMIN", "PROCESSOR"]),
            User.is_active == True
        ).all()
        
        for admin_user in admin_users:
            notification = Notification(
                user_id=admin_user.id,
                title=f"🚨 Admin Alert: {content['title']}",
                message=f"Claim {claim_id} requires attention: {content['message']}",
                notification_type="admin_alert",
                priority=content["priority"],
                related_resource_type="claim",
                related_resource_id=claim_id,
                delivery_channels=["in_app", "email"]
            )
            
            db.add(notification)
        
        db.commit()
        
        return {"admins_notified": len(admin_users)}
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task
def send_welcome_email(user_id: int):
    """
    Send welcome email to new user
    """
    try:
        db = next(get_database_session())
        
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"error": "User not found"}
        
        subject = "Welcome to Flogenix Enterprise!"
        
        email_body = f"""
        <html>
        <body>
            <h2>Welcome to Flogenix Enterprise, {user.first_name}!</h2>
            
            <p>Your account has been successfully created. You can now:</p>
            
            <ul>
                <li>Submit healthcare claims for processing</li>
                <li>Track your claim status in real-time</li>
                <li>View detailed processing reports</li>
                <li>Receive instant notifications</li>
            </ul>
            
            <p><strong>Account Details:</strong></p>
            <ul>
                <li>User ID: {user.user_id}</li>
                <li>Email: {user.email}</li>
                <li>Role: {user.role.value}</li>
            </ul>
            
            <p>If you have any questions, please contact our support team.</p>
            
            <p>Best regards,<br>The Flogenix Team</p>
        </body>
        </html>
        """
        
        email_sent = _send_email_notification(user.email, subject, email_body, user.first_name)
        
        # Create in-app notification
        notification = Notification(
            user_id=user.id,
            title="Welcome to Flogenix!",
            message="Your account has been created successfully. Start by submitting your first claim.",
            notification_type="welcome",
            priority="NORMAL",
            delivery_channels=["in_app"]
        )
        
        db.add(notification)
        db.commit()
        
        return {"email_sent": email_sent, "welcome_notification_created": True}
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task
def send_fraud_alert(claim_id: str, fraud_score: float, risk_factors: List[str]):
    """
    Send urgent fraud alert to security team
    """
    try:
        db = next(get_database_session())
        
        # Get claim details
        claim = db.query(Claim).filter(Claim.claim_id == claim_id).first()
        if not claim:
            return {"error": "Claim not found"}
        
        # Get security/admin users
        security_users = db.query(User).filter(
            User.role.in_(["ADMIN", "SUPER_ADMIN"]),
            User.is_active == True
        ).all()
        
        alert_title = f"🚨 FRAUD ALERT: High-risk claim detected"
        alert_message = f"""
        Fraud detection system flagged claim {claim_id} with high risk score.
        
        Fraud Score: {fraud_score}/100
        Risk Factors: {', '.join(risk_factors)}
        
        Patient: {claim.patient_name}
        Amount: ${claim.claim_amount:,.2f}
        Provider: {claim.provider_name}
        
        Immediate review required.
        """
        
        for user in security_users:
            notification = Notification(
                user_id=user.id,
                title=alert_title,
                message=alert_message,
                notification_type="fraud_alert",
                priority="URGENT",
                related_resource_type="claim",
                related_resource_id=claim_id,
                delivery_channels=["in_app", "email"]
            )
            
            db.add(notification)
            
            # Send immediate email
            _send_email_notification(
                user.email,
                alert_title,
                f"<html><body><h3>URGENT: Fraud Alert</h3><pre>{alert_message}</pre></body></html>",
                user.first_name
            )
        
        db.commit()
        
        return {"security_users_alerted": len(security_users)}
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task
def send_batch_notification(user_ids: List[int], title: str, message: str, notification_type: str = "system", priority: str = "NORMAL"):
    """
    Send notification to multiple users
    """
    try:
        db = next(get_database_session())
        
        notifications_created = 0
        
        for user_id in user_ids:
            user = db.query(User).filter(User.id == user_id).first()
            if user and user.is_active:
                notification = Notification(
                    user_id=user_id,
                    title=title,
                    message=message,
                    notification_type=notification_type,
                    priority=priority,
                    delivery_channels=["in_app"]
                )
                
                db.add(notification)
                notifications_created += 1
        
        db.commit()
        
        return {"notifications_created": notifications_created}
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if 'db' in locals():
            db.close()

@celery_app.task
def cleanup_old_notifications():
    """
    Clean up old read notifications
    """
    try:
        db = next(get_database_session())
        
        # Delete read notifications older than 30 days
        cutoff_date = datetime.utcnow() - timedelta(days=30)
        
        deleted_count = db.query(Notification).filter(
            Notification.is_read == True,
            Notification.read_at < cutoff_date
        ).delete()
        
        # Delete expired notifications
        expired_count = db.query(Notification).filter(
            Notification.expires_at < datetime.utcnow()
        ).delete()
        
        db.commit()
        
        return {
            "deleted_old_notifications": deleted_count,
            "deleted_expired_notifications": expired_count
        }
        
    except Exception as e:
        return {"error": str(e)}
    
    finally:
        if 'db' in locals():
            db.close()

def _create_status_notification_content(claim: Claim, new_status: str, decision: Optional[str], confidence_score: Optional[float]) -> Dict[str, Any]:
    """
    Create notification content based on claim status
    """
    status_messages = {
        ClaimStatus.PROCESSING.value: {
            "title": "Claim Processing Started",
            "message": f"Your claim {claim.claim_id} is now being processed by our AI system.",
            "priority": "NORMAL"
        },
        ClaimStatus.APPROVED.value: {
            "title": "✅ Claim Approved",
            "message": f"Great news! Your claim {claim.claim_id} for ${claim.claim_amount:,.2f} has been approved.",
            "priority": "NORMAL"
        },
        ClaimStatus.DENIED.value: {
            "title": "❌ Claim Denied",
            "message": f"Your claim {claim.claim_id} has been denied. Please review the details and contact us if you have questions.",
            "priority": "HIGH"
        },
        ClaimStatus.FRAUD_FLAGGED.value: {
            "title": "🚨 Claim Under Review",
            "message": f"Your claim {claim.claim_id} requires additional verification. Our team will review it shortly.",
            "priority": "HIGH"
        },
        ClaimStatus.PENDING_REVIEW.value: {
            "title": "⏳ Manual Review Required",
            "message": f"Your claim {claim.claim_id} requires manual review by our specialists.",
            "priority": "NORMAL"
        }
    }
    
    content = status_messages.get(new_status, {
        "title": "Claim Status Updated",
        "message": f"Your claim {claim.claim_id} status has been updated to {new_status}.",
        "priority": "NORMAL"
    })
    
    # Add decision and confidence info if available
    if decision and confidence_score:
        content["message"] += f" Decision: {decision} (Confidence: {confidence_score:.1f}%)"
    
    # Create email body
    content["email_body"] = f"""
    <html>
    <body>
        <h2>{content['title']}</h2>
        
        <p>Hello {claim.patient_name},</p>
        
        <p>{content['message']}</p>
        
        <h3>Claim Details:</h3>
        <ul>
            <li><strong>Claim ID:</strong> {claim.claim_id}</li>
            <li><strong>Patient:</strong> {claim.patient_name}</li>
            <li><strong>Amount:</strong> ${claim.claim_amount:,.2f}</li>
            <li><strong>Service Date:</strong> {claim.service_date}</li>
            <li><strong>Provider:</strong> {claim.provider_name}</li>
            <li><strong>Status:</strong> {new_status}</li>
        </ul>
        
        <p>You can view full details by logging into your Flogenix account.</p>
        
        <p>If you have any questions, please contact our support team.</p>
        
        <p>Best regards,<br>The Flogenix Team</p>
    </body>
    </html>
    """
    
    return content

def _send_email_notification(to_email: str, subject: str, body: str, first_name: str = "") -> bool:
    """
    Send email notification (mock implementation)
    In production, integrate with SendGrid, AWS SES, or similar service
    """
    try:
        # This is a mock implementation
        # In production, you would use a real email service
        
        print(f"📧 EMAIL SENT TO: {to_email}")
        print(f"📧 SUBJECT: {subject}")
        print(f"📧 RECIPIENT: {first_name}")
        print("📧 EMAIL CONTENT:")
        print(body)
        print("=" * 50)
        
        # Simulate email sending delay
        import time
        time.sleep(0.1)
        
        return True
        
    except Exception as e:
        print(f"Failed to send email: {e}")
        return False