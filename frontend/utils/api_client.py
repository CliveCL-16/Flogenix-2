import requests
import streamlit as st
from typing import Dict, List, Optional, Any
from datetime import date, datetime


class FlowgenixAPI:
    """API client for Flowgenix backend"""
    
    def __init__(self, base_url: str = "http://localhost:8000"):
        self.base_url = base_url.rstrip("/")
        self.api_url = f"{self.base_url}/api"
    
    def _make_request(self, method: str, endpoint: str, **kwargs) -> requests.Response:
        """Make HTTP request to API"""
        url = f"{self.api_url}{endpoint}"
        
        try:
            response = requests.request(method, url, timeout=30, **kwargs)
            return response
        except requests.exceptions.RequestException as e:
            st.error(f"API request failed: {e}")
            raise
    
    def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            response = self._make_request("GET", "/health")
            return response.status_code == 200
        except:
            return False
    
    def submit_claim(self, claim_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Submit a new claim"""
        try:
            # Convert date objects to strings for JSON serialization
            if isinstance(claim_data.get('service_date'), date):
                claim_data['service_date'] = claim_data['service_date'].isoformat()
            
            response = self._make_request("POST", "/claims/submit", json=claim_data)
            
            if response.status_code == 200:
                return response.json()
            else:
                error_detail = response.json().get('detail', 'Unknown error')
                st.error(f"Failed to submit claim: {error_detail}")
                return None
                
        except Exception as e:
            st.error(f"Error submitting claim: {e}")
            return None
    
    def get_claims(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all claims, optionally filtered by status"""
        try:
            params = {}
            if status_filter:
                params['status'] = status_filter
            
            response = self._make_request("GET", "/claims", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to get claims: {response.status_code}")
                return []
                
        except Exception as e:
            st.error(f"Error getting claims: {e}")
            return []
    
    def get_claim_details(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a specific claim"""
        try:
            response = self._make_request("GET", f"/claims/{claim_id}")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                st.error("Claim not found")
                return None
            else:
                st.error(f"Failed to get claim details: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error getting claim details: {e}")
            return None
    
    def process_claim(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Process a pending claim"""
        try:
            response = self._make_request("POST", f"/claims/{claim_id}/process")
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 404:
                st.error("Claim not found")
                return None
            elif response.status_code == 400:
                error_detail = response.json().get('detail', 'Bad request')
                st.error(f"Cannot process claim: {error_detail}")
                return None
            else:
                st.error(f"Failed to process claim: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error processing claim: {e}")
            return None
    
    def get_fraud_analysis(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get fraud analysis for a claim"""
        try:
            response = self._make_request("GET", f"/claims/{claim_id}/fraud-analysis")
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            st.error(f"Error getting fraud analysis: {e}")
            return None
    
    def get_dashboard_metrics(self) -> Optional[Dict[str, Any]]:
        """Get dashboard metrics"""
        try:
            response = self._make_request("GET", "/dashboard/metrics")
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to get dashboard metrics: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error getting dashboard metrics: {e}")
            return None
    
    def handle_exception(self, claim_id: str, exception_type: str, exception_details: str = "") -> Optional[Dict[str, Any]]:
        """Handle an exception for a claim"""
        try:
            params = {
                "exception_type": exception_type,
                "exception_details": exception_details
            }
            response = self._make_request("POST", f"/claims/{claim_id}/handle-exception", params=params)
            
            if response.status_code == 200:
                return response.json()
            else:
                st.error(f"Failed to handle exception: {response.status_code}")
                return None
                
        except Exception as e:
            st.error(f"Error handling exception: {e}")
            return None
    
    def get_agent_timeline(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get agent processing timeline for a claim"""
        try:
            response = self._make_request("GET", f"/claims/{claim_id}/agent-timeline")
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            st.error(f"Error getting agent timeline: {e}")
            return None
    
    def get_agent_reasoning(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get agent reasoning steps for a claim"""
        try:
            response = self._make_request("GET", f"/claims/{claim_id}/agent-reasoning")
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            st.error(f"Error getting agent reasoning: {e}")
            return None
    
    def get_tool_usage(self, claim_id: str) -> Optional[Dict[str, Any]]:
        """Get tool usage for a claim"""
        try:
            response = self._make_request("GET", f"/claims/{claim_id}/tool-usage")
            
            if response.status_code == 200:
                return response.json()
            else:
                return None
                
        except Exception as e:
            st.error(f"Error getting tool usage: {e}")
            return None


# Initialize API client
@st.cache_resource
def get_api_client():
    return FlowgenixAPI()


def format_currency(amount: float) -> str:
    """Format amount as currency"""
    return f"${amount:,.2f}"


def format_datetime(dt_str: str) -> str:
    """Format datetime string for display"""
    try:
        dt = datetime.fromisoformat(dt_str.replace('Z', '+00:00'))
        return dt.strftime("%Y-%m-%d %H:%M")
    except:
        return dt_str


def get_status_color(status: str) -> str:
    """Get color for claim status"""
    colors = {
        "PENDING": "🟡",
        "APPROVED": "🟢", 
        "DENIED": "🔴",
        "PENDING_REVIEW": "🟠",
        "FRAUD_FLAGGED": "🚫"
    }
    return colors.get(status, "⚪")


def get_status_style(status: str) -> str:
    """Get CSS style for claim status"""
    styles = {
        "PENDING": "background-color: #FFF3CD; color: #856404; padding: 4px 8px; border-radius: 4px;",
        "APPROVED": "background-color: #D4EDDA; color: #155724; padding: 4px 8px; border-radius: 4px;",
        "DENIED": "background-color: #F8D7DA; color: #721C24; padding: 4px 8px; border-radius: 4px;",
        "PENDING_REVIEW": "background-color: #FCF4DD; color: #CC8A00; padding: 4px 8px; border-radius: 4px;",
        "FRAUD_FLAGGED": "background-color: #F5C6CB; color: #721C24; padding: 4px 8px; border-radius: 4px;"
    }
    return styles.get(status, "padding: 4px 8px; border-radius: 4px;")