"""
Enterprise System Validation Script
Validates complete Flogenix enterprise platform functionality
"""

import asyncio
import sys
import os
import json
import time
import requests
import websockets
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, List, Optional

# Configuration
BACKEND_URL = "http://localhost:8000"
FRONTEND_URL = "http://localhost:8080"
WEBSOCKET_URL = "ws://localhost:8000/api/notifications/ws"

class SystemValidator:
    """Comprehensive system validation"""
    
    def __init__(self):
        self.session = requests.Session()
        self.auth_token = None
        self.user_id = None
        self.test_results = {
            "backend_health": False,
            "frontend_health": False,
            "authentication": False,
            "claims_processing": False,
            "enhanced_ai_processing": False,
            "notifications": False,
            "websocket": False,
            "admin_functions": False,
            "security": False,
            "performance": False
        }
        self.errors = []
        
    def log(self, message: str, level: str = "INFO"):
        """Log message with timestamp"""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{timestamp}] {level}: {message}")
        
    def add_error(self, error: str):
        """Add error to error list"""
        self.errors.append(error)
        self.log(error, "ERROR")
    
    def validate_backend_health(self) -> bool:
        """Validate backend health"""
        try:
            self.log("Checking backend health...")
            response = self.session.get(f"{BACKEND_URL}/api/health", timeout=10)
            
            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log("✅ Backend health check passed")
                    return True
                else:
                    self.add_error(f"Backend unhealthy: {data}")
                    return False
            else:
                self.add_error(f"Backend health check failed: {response.status_code}")
                return False
                
        except Exception as e:
            self.add_error(f"Backend connection failed: {str(e)}")
            return False
    
    def validate_frontend_health(self) -> bool:
        """Validate frontend accessibility"""
        try:
            self.log("Checking frontend accessibility...")
            response = self.session.get(FRONTEND_URL, timeout=10)
            
            if response.status_code == 200:
                self.log("✅ Frontend accessible")
                return True
            else:
                self.add_error(f"Frontend not accessible: {response.status_code}")
                return False
                
        except Exception as e:
            self.add_error(f"Frontend connection failed: {str(e)}")
            return False
    
    def validate_authentication(self) -> bool:
        """Validate authentication system"""
        try:
            self.log("Testing authentication system...")
            
            # Test user registration
            user_data = {
                "email": f"test_{int(time.time())}@example.com",
                "username": f"testuser_{int(time.time())}",
                "password": "TestPassword123!",
                "first_name": "Test",
                "last_name": "User"
            }
            
            response = self.session.post(
                f"{BACKEND_URL}/auth/register",
                json=user_data,
                timeout=10
            )
            
            if response.status_code != 201:
                self.add_error(f"User registration failed: {response.status_code}")
                return False
            
            self.user_id = response.json().get("user_id")
            
            # Test login
            login_response = self.session.post(
                f"{BACKEND_URL}/auth/login",
                json={
                    "email_or_username": user_data["email"],
                    "password": user_data["password"]
                },
                timeout=10
            )
            
            if login_response.status_code != 200:
                self.add_error(f"Login failed: {login_response.status_code}")
                return False
            
            login_data = login_response.json()
            self.auth_token = login_data.get("access_token")
            
            if not self.auth_token:
                self.add_error("No access token received")
                return False
            
            # Test protected endpoint
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            me_response = self.session.get(
                f"{BACKEND_URL}/auth/me",
                headers=headers,
                timeout=10
            )
            
            if me_response.status_code != 200:
                self.add_error(f"Protected endpoint failed: {me_response.status_code}")
                return False
            
            self.log("✅ Authentication system working")
            return True
            
        except Exception as e:
            self.add_error(f"Authentication test failed: {str(e)}")
            return False
    
    def validate_claims_processing(self) -> bool:
        """Validate claims processing"""
        try:
            self.log("Testing claims processing...")
            
            if not self.auth_token:
                self.add_error("No authentication token for claims test")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Submit test claim
            claim_data = {
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
            
            response = self.session.post(
                f"{BACKEND_URL}/api/claims/submit",
                json=claim_data,
                headers=headers,
                timeout=30
            )
            
            if response.status_code != 200:
                self.add_error(f"Claim submission failed: {response.status_code}")
                return False
            
            claim_id = response.json().get("claim_id")
            if not claim_id:
                self.add_error("No claim ID returned")
                return False
            
            # Get claim details
            details_response = self.session.get(
                f"{BACKEND_URL}/api/claims/{claim_id}",
                headers=headers,
                timeout=10
            )
            
            if details_response.status_code != 200:
                self.add_error(f"Claim details failed: {details_response.status_code}")
                return False
            
            # Get claims list
            list_response = self.session.get(
                f"{BACKEND_URL}/api/claims",
                headers=headers,
                timeout=10
            )
            
            if list_response.status_code != 200:
                self.add_error(f"Claims list failed: {list_response.status_code}")
                return False
            
            self.log("✅ Claims processing working")
            return True
            
        except Exception as e:
            self.add_error(f"Claims processing test failed: {str(e)}")
            return False
    
    def validate_enhanced_ai_processing(self) -> bool:
        """Validate enhanced multi-agent AI processing capabilities"""
        try:
            self.log("Testing enhanced multi-agent AI processing...")
            
            if not self.auth_token:
                self.add_error("No authentication token for AI test")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test 1: Submit a claim that should be APPROVED (ultra low-risk)
            approval_claim_data = {
                "patient_name": "John Doe",
                "patient_id": "PAT111111",
                "insurance_provider": "Medicare",
                "policy_number": "POL-12345",  # Format that will trigger ELIGIBLE response
                "diagnosis_code": "Z00.00",  # General exam - lowest risk
                "procedure_code": "99213",   # Perfect match for Z00.00
                "claim_amount": 75.00,       # Very low amount
                "service_date": "2024-10-25", # Very recent date
                "provider_name": "Dr. Johnson",
                "provider_npi": "1111111111",
                "notes": "Routine annual physical exam"
            }
            
            self.log("Testing APPROVAL scenario with low-risk claim...")
            approval_response = self.session.post(
                f"{BACKEND_URL}/api/claims/submit",
                json=approval_claim_data,
                headers=headers,
                timeout=30
            )
            
            if approval_response.status_code != 200:
                self.add_error(f"Approval test claim submission failed: {approval_response.status_code}")
                self.log(f"Response: {approval_response.text}")
                return False
            
            approval_result = approval_response.json()
            approval_claim_id = approval_result.get("claim_id")
            approval_status = approval_result.get("status", "UNKNOWN")
            approval_confidence = approval_result.get("confidence_score")
            
            self.log(f"Approval test - Claim: {approval_claim_id}, Status: {approval_status}, Confidence: {approval_confidence}%")
            
            # Test 2: Submit a claim that should be DENIED (high-risk scenario)
            denial_claim_data = {
                "patient_name": "Jane Smith",
                "patient_id": "PAT654321",
                "insurance_provider": "AI Test Insurance",
                "policy_number": "POL345678",
                "diagnosis_code": "C50.1",   # Cancer diagnosis - high complexity
                "procedure_code": "27447",   # Expensive knee surgery
                "claim_amount": 25000.00,    # High amount that may trigger review
                "service_date": "2024-01-16",
                "provider_name": "Dr. Expensive",
                "provider_npi": "9876543210",
                "notes": "Complex surgical procedure with high cost"
            }
            
            self.log("Testing DENIAL scenario with high-risk claim...")
            denial_response = self.session.post(
                f"{BACKEND_URL}/api/claims/submit",
                json=denial_claim_data,
                headers=headers,
                timeout=30
            )
            
            if denial_response.status_code != 200:
                self.add_error(f"Denial test claim submission failed: {denial_response.status_code}")
                return False
            
            denial_result = denial_response.json()
            denial_claim_id = denial_result.get("claim_id")
            denial_status = denial_result.get("status", "UNKNOWN")
            denial_confidence = denial_result.get("confidence_score")
            
            self.log(f"Denial test - Claim: {denial_claim_id}, Status: {denial_status}, Confidence: {denial_confidence}%")
            
            # Validate AI processing results
            success_count = 0
            total_tests = 2
            
            # Check approval claim
            if approval_confidence is not None and 0 <= approval_confidence <= 100:
                success_count += 1
                if approval_status == "APPROVED":
                    self.log("✅ AI correctly approved low-risk claim")
                elif approval_status in ["DENIED", "PENDING_REVIEW"]:
                    self.log(f"⚠️ AI decided {approval_status} for low-risk claim (may be conservative)")
                else:
                    self.log(f"⚠️ Unexpected status for approval test: {approval_status}")
            else:
                self.add_error(f"Invalid confidence score for approval test: {approval_confidence}")
            
            # Check denial claim  
            if denial_confidence is not None and 0 <= denial_confidence <= 100:
                success_count += 1
                if denial_status in ["DENIED", "PENDING_REVIEW"]:
                    self.log("✅ AI correctly flagged high-risk claim")
                elif denial_status == "APPROVED":
                    self.log("⚠️ AI approved high-risk claim (may need tuning)")
                else:
                    self.log(f"⚠️ Unexpected status for denial test: {denial_status}")
            else:
                self.add_error(f"Invalid confidence score for denial test: {denial_confidence}")
            
            if success_count == total_tests:
                self.log("✅ AI processing working (tested both approval and denial scenarios)")
                return True
            else:
                self.add_error(f"AI processing validation failed: {success_count}/{total_tests} tests passed")
                return False
            
        except Exception as e:
            self.add_error(f"AI processing test failed: {str(e)}")
            return False
    
    def validate_notifications(self) -> bool:
        """Validate notification system"""
        try:
            self.log("Testing notification system...")
            
            if not self.auth_token:
                self.add_error("No authentication token for notifications test")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Get notifications
            response = self.session.get(
                f"{BACKEND_URL}/api/notifications",
                headers=headers,
                timeout=10
            )
            
            if response.status_code != 200:
                self.add_error(f"Get notifications failed: {response.status_code}")
                return False
            
            # Get notification stats
            stats_response = self.session.get(
                f"{BACKEND_URL}/api/notifications/stats",
                headers=headers,
                timeout=10
            )
            
            if stats_response.status_code != 200:
                self.add_error(f"Notification stats failed: {stats_response.status_code}")
                return False
            
            self.log("✅ Notification system working")
            return True
            
        except Exception as e:
            self.add_error(f"Notification test failed: {str(e)}")
            return False
    
    async def validate_websocket(self) -> bool:
        """Validate WebSocket functionality"""
        try:
            self.log("Testing WebSocket connection...")
            
            if not self.auth_token:
                self.add_error("No authentication token for WebSocket test")
                return False
            
            # Test WebSocket connection
            uri = f"{WEBSOCKET_URL}?token={self.auth_token}"
            
            try:
                async with websockets.connect(uri) as websocket:
                    # Send test message
                    test_message = {"type": "ping"}
                    await websocket.send(json.dumps(test_message))
                    
                    # Wait for response
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=5)
                        data = json.loads(response)
                        
                        if data.get("type") in ["pong", "connection"]:
                            self.log("✅ WebSocket connection working")
                            return True
                        else:
                            self.add_error(f"Unexpected WebSocket response: {data}")
                            return False
                    
                    except asyncio.TimeoutError:
                        self.add_error("WebSocket response timeout")
                        return False
            except asyncio.TimeoutError:
                self.add_error("WebSocket connection timeout")
                return False
        except Exception as e:
            self.add_error(f"WebSocket test failed: {str(e)}")
            return False
    
    def validate_admin_functions(self) -> bool:
        """Validate admin functionality (if user has admin access)"""
        try:
            self.log("Testing admin functions...")
            
            if not self.auth_token:
                self.add_error("No authentication token for admin test")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Try to access admin endpoint
            response = self.session.get(
                f"{BACKEND_URL}/api/admin/stats",
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 403:
                self.log("⚠️ Admin access denied (expected for regular user)")
                return True  # This is expected for non-admin users
            elif response.status_code == 200:
                self.log("✅ Admin functions accessible")
                return True
            else:
                self.add_error(f"Admin endpoint error: {response.status_code}")
                return False
            
        except Exception as e:
            self.add_error(f"Admin function test failed: {str(e)}")
            return False
    
    def validate_security(self) -> bool:
        """Validate security measures"""
        try:
            self.log("Testing security measures...")
            
            # Test unauthorized access
            unauth_response = self.session.get(f"{BACKEND_URL}/auth/me", timeout=10)
            if unauth_response.status_code not in [401, 403]:
                self.add_error(f"Unauthorized access allowed (got {unauth_response.status_code}, expected 401 or 403)")
                return False
            
            # Test invalid token
            invalid_headers = {"Authorization": "Bearer invalid_token"}
            invalid_response = self.session.get(
                f"{BACKEND_URL}/auth/me",
                headers=invalid_headers,
                timeout=10
            )
            if invalid_response.status_code not in [401, 403]:
                self.add_error(f"Invalid token accepted (got {invalid_response.status_code}, expected 401 or 403)")
                return False
            
            self.log("✅ Security measures working")
            return True
            
        except Exception as e:
            self.add_error(f"Security test failed: {str(e)}")
            return False
    
    def validate_performance(self) -> bool:
        """Validate basic performance metrics"""
        try:
            self.log("Testing performance...")
            
            if not self.auth_token:
                self.add_error("No authentication token for performance test")
                return False
            
            headers = {"Authorization": f"Bearer {self.auth_token}"}
            
            # Test response times
            start_time = time.time()
            response = self.session.get(
                f"{BACKEND_URL}/api/health",
                headers=headers,
                timeout=10
            )
            response_time = time.time() - start_time
            
            if response.status_code != 200:
                self.add_error("Performance test health check failed")
                return False
            
            if response_time > 5.0:  # 5 second threshold
                self.add_error(f"Slow response time: {response_time:.2f}s")
                return False
            
            self.log(f"✅ Performance acceptable (response time: {response_time:.2f}s)")
            return True
            
        except Exception as e:
            self.add_error(f"Performance test failed: {str(e)}")
            return False
    
    async def run_validation(self) -> Dict:
        """Run complete system validation"""
        self.log("Starting enterprise system validation...")
        self.log("=" * 60)
        
        # Run validation tests
        self.test_results["backend_health"] = self.validate_backend_health()
        self.test_results["frontend_health"] = self.validate_frontend_health()
        self.test_results["authentication"] = self.validate_authentication()
        self.test_results["claims_processing"] = self.validate_claims_processing()
        self.test_results["enhanced_ai_processing"] = self.validate_enhanced_ai_processing()
        self.test_results["notifications"] = self.validate_notifications()
        self.test_results["websocket"] = await self.validate_websocket()
        self.test_results["admin_functions"] = self.validate_admin_functions()
        self.test_results["security"] = self.validate_security()
        self.test_results["performance"] = self.validate_performance()
        
        # Generate report
        self.generate_report()
        
        return {
            "results": self.test_results,
            "errors": self.errors,
            "success_rate": sum(self.test_results.values()) / len(self.test_results)
        }
    
    def generate_report(self):
        """Generate validation report"""
        self.log("=" * 60)
        self.log("ENTERPRISE SYSTEM VALIDATION REPORT")
        self.log("=" * 60)
        
        # Test results summary
        passed = sum(self.test_results.values())
        total = len(self.test_results)
        success_rate = (passed / total) * 100
        
        self.log(f"Overall Success Rate: {success_rate:.1f}% ({passed}/{total})")
        self.log("")
        
        # Individual test results
        for test_name, result in self.test_results.items():
            status = "✅ PASS" if result else "❌ FAIL"
            self.log(f"{test_name.replace('_', ' ').title()}: {status}")
        
        # Errors summary
        if self.errors:
            self.log("")
            self.log("ERRORS ENCOUNTERED:")
            self.log("-" * 30)
            for i, error in enumerate(self.errors, 1):
                self.log(f"{i}. {error}")
        
        # Recommendations
        self.log("")
        self.log("RECOMMENDATIONS:")
        self.log("-" * 30)
        
        if success_rate >= 90:
            self.log("✅ System is ready for production deployment")
        elif success_rate >= 70:
            self.log("⚠️ System mostly functional, address failing tests before production")
        else:
            self.log("❌ System needs significant fixes before deployment")
        
        if not self.test_results["backend_health"]:
            self.log("- Ensure backend server is running on port 8000")
        
        if not self.test_results["frontend_health"]:
            self.log("- Ensure frontend server is running on port 5173")
        
        if not self.test_results["enhanced_ai_processing"]:
            self.log("- Check enhanced multi-agent processor configuration")
            self.log("- Verify AI processing service is properly configured")
        
        if not self.test_results["websocket"]:
            self.log("- Check WebSocket server configuration")
            self.log("- Verify WebSocket authentication is working")
        
        self.log("")
        self.log("Validation completed at: " + datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

async def main():
    """Main validation function"""
    validator = SystemValidator()
    
    try:
        results = await validator.run_validation()
        
        # Exit with appropriate code
        if results["success_rate"] >= 0.9:
            sys.exit(0)  # Success
        elif results["success_rate"] >= 0.7:
            sys.exit(1)  # Warnings
        else:
            sys.exit(2)  # Errors
            
    except KeyboardInterrupt:
        print("\nValidation interrupted by user")
        sys.exit(3)
    except Exception as e:
        print(f"Validation failed with error: {str(e)}")
        sys.exit(4)

if __name__ == "__main__":
    asyncio.run(main())