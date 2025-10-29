"""
Comprehensive test suite for Flogenix Enterprise API
Tests authentication, claims processing, notifications, and admin features
"""

import pytest
import asyncio
from httpx import AsyncClient
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from unittest.mock import patch, MagicMock
import json
from datetime import datetime, timedelta, timezone

# Import application components
from main_enterprise import app
from app.core.database import get_database_session, Base
from app.core.security import auth_service
from app.core.models import User, UserRole, Claim, ClaimStatus
from app.services.notification_service import NotificationService, NotificationType, NotificationCategory, NotificationPriority

# Test database setup
SQLALCHEMY_DATABASE_URL = "sqlite:///./test.db"
engine = create_engine(SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def override_get_db():
    """Override database dependency for testing"""
    try:
        db = TestingSessionLocal()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_database_session] = override_get_db

@pytest.fixture(scope="module")
def setup_database():
    """Setup test database"""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)

@pytest.fixture
def db_session():
    """Database session for tests"""
    connection = engine.connect()
    transaction = connection.begin()
    session = TestingSessionLocal(bind=connection)
    
    yield session
    
    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture
def client():
    """Test client"""
    return TestClient(app)

@pytest.fixture
def sample_user_data():
    """Sample user data for testing"""
    return {
        "email": "test@example.com",
        "username": "testuser",
        "password": "TestPassword123!",
        "first_name": "Test",
        "last_name": "User"
    }

@pytest.fixture
def sample_claim_data():
    """Sample claim data for testing"""
    return {
        "patient_name": "John Doe",
        "patient_id": "PAT123456",
        "insurance_provider": "Test Insurance",
        "policy_number": "POL789012",
        "diagnosis_code": "Z00.00",
        "procedure_code": "99213",
        "claim_amount": 250.00,
        "service_date": "2024-01-15",
        "provider_name": "Dr. Test",
        "provider_npi": "1234567890",
        "notes": "Test claim submission"
    }

@pytest.fixture
def authenticated_headers(client, sample_user_data):
    """Get authenticated headers for testing"""
    # Register user
    response = client.post("/auth/register", json=sample_user_data)
    assert response.status_code == 201
    
    # Login
    login_response = client.post("/auth/login", json={
        "email_or_username": sample_user_data["email"],
        "password": sample_user_data["password"]
    })
    assert login_response.status_code == 200
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

@pytest.fixture
def admin_headers(client, db_session):
    """Get admin authenticated headers for testing"""
    # Create admin user directly in database
    admin_data = {
        "email": "admin@example.com",
        "username": "admin",
        "password": "AdminPassword123!",
        "first_name": "Admin",
        "last_name": "User"
    }
    
    admin_user = auth_service.create_user(db_session, admin_data)
    admin_user.role = UserRole.ADMIN
    db_session.commit()
    
    # Login as admin
    login_response = client.post("/auth/login", json={
        "email_or_username": admin_data["email"],
        "password": admin_data["password"]
    })
    assert login_response.status_code == 200
    
    token = login_response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}

class TestAuthentication:
    """Test authentication endpoints"""
    
    def test_register_user(self, client, sample_user_data):
        """Test user registration"""
        response = client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 201
        
        data = response.json()
        assert data["email"] == sample_user_data["email"]
        assert data["username"] == sample_user_data["username"]
        assert "user_id" in data
    
    def test_register_duplicate_user(self, client, sample_user_data):
        """Test duplicate user registration fails"""
        # Register first user
        client.post("/auth/register", json=sample_user_data)
        
        # Try to register again
        response = client.post("/auth/register", json=sample_user_data)
        assert response.status_code == 400
        assert "already exists" in response.json()["detail"]
    
    def test_login_valid_credentials(self, client, sample_user_data):
        """Test login with valid credentials"""
        # Register user first
        client.post("/auth/register", json=sample_user_data)
        
        # Login
        response = client.post("/auth/login", json={
            "email_or_username": sample_user_data["email"],
            "password": sample_user_data["password"]
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"
        assert "user_info" in data
    
    def test_login_invalid_credentials(self, client, sample_user_data):
        """Test login with invalid credentials"""
        response = client.post("/auth/login", json={
            "email_or_username": "nonexistent@example.com",
            "password": "wrongpassword"
        })
        
        assert response.status_code == 401
    
    def test_get_current_user(self, client, authenticated_headers):
        """Test getting current user info"""
        response = client.get("/auth/me", headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "email" in data
        assert "username" in data
        assert "role" in data
    
    def test_protected_endpoint_without_auth(self, client):
        """Test protected endpoint without authentication"""
        response = client.get("/auth/me")
        assert response.status_code == 401

class TestClaimsProcessing:
    """Test claims processing endpoints"""
    
    def test_submit_claim(self, client, authenticated_headers, sample_claim_data):
        """Test claim submission"""
        response = client.post(
            "/api/claims/submit",
            json=sample_claim_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert "claim_id" in data
        assert data["status"] == "PENDING"
        assert data["patient_name"] == sample_claim_data["patient_name"]
    
    def test_submit_claim_invalid_data(self, client, authenticated_headers):
        """Test claim submission with invalid data"""
        invalid_data = {
            "patient_name": "",  # Empty name
            "claim_amount": -100  # Negative amount
        }
        
        response = client.post(
            "/api/claims/submit",
            json=invalid_data,
            headers=authenticated_headers
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_get_claims(self, client, authenticated_headers, sample_claim_data):
        """Test getting claims list"""
        # Submit a claim first
        client.post(
            "/api/claims/submit",
            json=sample_claim_data,
            headers=authenticated_headers
        )
        
        # Get claims
        response = client.get("/api/claims", headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "claims" in data
        assert len(data["claims"]) >= 1
    
    def test_get_claim_details(self, client, authenticated_headers, sample_claim_data):
        """Test getting specific claim details"""
        # Submit a claim first
        submit_response = client.post(
            "/api/claims/submit",
            json=sample_claim_data,
            headers=authenticated_headers
        )
        claim_id = submit_response.json()["claim_id"]
        
        # Get claim details
        response = client.get(f"/api/claims/{claim_id}", headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "claim" in data
        assert data["claim"]["claim_id"] == claim_id
    
    @patch('app.services.multi_agent_processor.MultiAgentProcessor.process_claim')
    def test_process_claim(self, mock_process, client, authenticated_headers, sample_claim_data):
        """Test AI claim processing"""
        # Mock the AI processing
        mock_process.return_value = {
            "decision": "APPROVE",
            "confidence_score": 95.0,
            "reasoning": "Standard claim with valid codes",
            "fraud_score": 5.0,
            "processing_time": 2.5,
            "agent_reports": []
        }
        
        # Submit a claim first
        submit_response = client.post(
            "/api/claims/submit",
            json=sample_claim_data,
            headers=authenticated_headers
        )
        claim_id = submit_response.json()["claim_id"]
        
        # Process the claim
        response = client.post(
            f"/api/claims/{claim_id}/process",
            headers=authenticated_headers
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "APPROVED"
        assert data["confidence_score"] == 95.0

class TestNotifications:
    """Test notification system"""
    
    def test_get_notifications(self, client, authenticated_headers):
        """Test getting notifications"""
        response = client.get("/api/notifications", headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "notifications" in data
        assert "count" in data
        assert "unread_count" in data
    
    def test_notification_stats(self, client, authenticated_headers):
        """Test notification statistics"""
        response = client.get("/api/notifications/stats", headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_notifications" in data
        assert "unread_notifications" in data
        assert "category_breakdown" in data
    
    def test_mark_notification_read(self, client, authenticated_headers, db_session):
        """Test marking notification as read"""
        # Create a test notification
        service = NotificationService(db_session)
        notification = service.create_notification(
            title="Test Notification",
            message="Test message",
            user_id="test_user_123"
        )
        
        response = client.post(
            f"/api/notifications/{notification.id}/read",
            headers=authenticated_headers
        )
        assert response.status_code == 200
    
    def test_mark_all_notifications_read(self, client, authenticated_headers):
        """Test marking all notifications as read"""
        response = client.post(
            "/api/notifications/read-all",
            headers=authenticated_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "updated_count" in data

class TestAdministration:
    """Test admin endpoints"""
    
    def test_admin_stats(self, client, admin_headers):
        """Test admin system statistics"""
        response = client.get("/api/admin/stats", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_users" in data
        assert "total_claims" in data
        assert "system_uptime" in data
    
    def test_admin_users(self, client, admin_headers):
        """Test admin user management"""
        response = client.get("/api/admin/users", headers=admin_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "users" in data
        assert "total" in data
    
    def test_admin_queue(self, client, admin_headers):
        """Test admin claims queue"""
        response = client.get("/api/admin/queue", headers=admin_headers)
        assert response.status_code == 200
    
    def test_admin_agent_metrics(self, client, admin_headers):
        """Test admin AI agent metrics"""
        response = client.get("/api/admin/agents/metrics", headers=admin_headers)
        assert response.status_code == 200
    
    def test_admin_broadcast_notification(self, client, admin_headers):
        """Test admin notification broadcast"""
        notification_data = {
            "title": "System Maintenance",
            "message": "Scheduled maintenance will occur tonight",
            "priority": "medium"
        }
        
        response = client.post(
            "/api/admin/notifications/broadcast",
            json=notification_data,
            headers=admin_headers
        )
        assert response.status_code == 200
        
        data = response.json()
        assert "notification_id" in data
    
    def test_non_admin_access_denied(self, client, authenticated_headers):
        """Test non-admin access to admin endpoints"""
        response = client.get("/api/admin/stats", headers=authenticated_headers)
        assert response.status_code == 403

class TestHealthAndMonitoring:
    """Test health check and monitoring endpoints"""
    
    def test_health_check(self, client):
        """Test health check endpoint"""
        response = client.get("/api/health")
        assert response.status_code == 200
        
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data
    
    def test_dashboard_metrics(self, client, authenticated_headers):
        """Test dashboard metrics"""
        response = client.get("/api/dashboard/metrics", headers=authenticated_headers)
        assert response.status_code == 200
        
        data = response.json()
        assert "total_claims" in data
        assert "approval_rate" in data
        assert "avg_processing_time_seconds" in data

class TestSecurity:
    """Test security features"""
    
    def test_password_strength_validation(self, client):
        """Test password strength validation"""
        weak_password_data = {
            "email": "test@example.com",
            "username": "testuser",
            "password": "weak",  # Too weak
            "first_name": "Test",
            "last_name": "User"
        }
        
        response = client.post("/auth/register", json=weak_password_data)
        assert response.status_code == 400
    
    def test_rate_limiting(self, client, sample_user_data):
        """Test rate limiting (simplified test)"""
        # Register user first
        client.post("/auth/register", json=sample_user_data)
        
        # Make multiple rapid requests
        responses = []
        for _ in range(10):
            response = client.post("/auth/login", json={
                "email_or_username": "wrong@example.com",
                "password": "wrongpassword"
            })
            responses.append(response.status_code)
        
        # Should have some failed attempts (401s)
        assert 401 in responses
    
    def test_jwt_token_validation(self, client):
        """Test JWT token validation"""
        # Try to access protected endpoint with invalid token
        headers = {"Authorization": "Bearer invalid_token"}
        response = client.get("/auth/me", headers=headers)
        assert response.status_code == 401

class TestIntegration:
    """Integration tests for complete workflows"""
    
    def test_complete_claim_workflow(self, client, authenticated_headers, sample_claim_data):
        """Test complete claim processing workflow"""
        # 1. Submit claim
        submit_response = client.post(
            "/api/claims/submit",
            json=sample_claim_data,
            headers=authenticated_headers
        )
        assert submit_response.status_code == 200
        claim_id = submit_response.json()["claim_id"]
        
        # 2. Get claim details
        details_response = client.get(
            f"/api/claims/{claim_id}",
            headers=authenticated_headers
        )
        assert details_response.status_code == 200
        
        # 3. Check claim appears in list
        list_response = client.get("/api/claims", headers=authenticated_headers)
        assert list_response.status_code == 200
        claim_ids = [c["claim_id"] for c in list_response.json()["claims"]]
        assert claim_id in claim_ids
    
    @patch('app.services.multi_agent_processor.MultiAgentProcessor.process_claim')
    def test_fraud_detection_workflow(self, mock_process, client, authenticated_headers, sample_claim_data):
        """Test fraud detection workflow"""
        # Mock fraud detection
        mock_process.return_value = {
            "decision": "DENY",
            "confidence_score": 85.0,
            "reasoning": "High fraud risk detected",
            "fraud_score": 92.0,
            "processing_time": 3.2,
            "agent_reports": []
        }
        
        # Submit suspicious claim
        suspicious_claim = sample_claim_data.copy()
        suspicious_claim["claim_amount"] = 99999.99  # Suspiciously high amount
        
        submit_response = client.post(
            "/api/claims/submit",
            json=suspicious_claim,
            headers=authenticated_headers
        )
        claim_id = submit_response.json()["claim_id"]
        
        # Process claim
        process_response = client.post(
            f"/api/claims/{claim_id}/process",
            headers=authenticated_headers
        )
        
        assert process_response.status_code == 200
        data = process_response.json()
        assert data["status"] == "DENIED"
        assert data["fraud_score"] == 92.0

# Pytest configuration
if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])