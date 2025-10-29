"""
Authentication API routes for enterprise application
Provides JWT-based authentication with role-based access control
"""

from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from pydantic import BaseModel, EmailStr, Field

from app.core.database import get_database_session
from app.core.security import (
    auth_service, 
    security_service,
    get_current_user, 
    log_audit_event,
    AuditAction
)
from app.core.models import User, UserRole

# Security scheme
security = HTTPBearer()

# Router
router = APIRouter()

# Request/Response models
class UserCreate(BaseModel):
    """User registration model"""
    email: EmailStr = Field(..., description="User email address")
    username: str = Field(..., min_length=3, max_length=50, description="Username")
    password: str = Field(..., min_length=8, description="Password")
    first_name: str = Field(..., min_length=1, max_length=50, description="First name")
    last_name: str = Field(..., min_length=1, max_length=50, description="Last name")

class UserLogin(BaseModel):
    """User login model"""
    email_or_username: str = Field(..., description="Email or username")
    password: str = Field(..., description="Password")
    totp_code: Optional[str] = Field(None, description="Two-factor authentication code")

class TokenResponse(BaseModel):
    """Token response model"""
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: dict

class PasswordChange(BaseModel):
    """Password change model"""
    current_password: str
    new_password: str = Field(..., min_length=8)

class TwoFactorSetup(BaseModel):
    """Two-factor authentication setup"""
    totp_code: str = Field(..., description="TOTP code for verification")

class UserProfile(BaseModel):
    """User profile response"""
    id: str
    user_id: str
    email: str
    username: str
    first_name: str
    last_name: str
    role: str
    two_factor_enabled: bool
    is_active: bool
    created_at: datetime
    last_login_at: Optional[datetime]

@router.post("/register", response_model=dict, status_code=status.HTTP_201_CREATED)
async def register_user(
    user_data: UserCreate,
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    Register a new user account
    
    Creates a new user with the provided information.
    Email and username must be unique.
    """
    try:
        # Check if user already exists
        existing_user = auth_service.get_user_by_email_or_username(db, user_data.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        existing_user = auth_service.get_user_by_email_or_username(db, user_data.username)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this username already exists"
            )
        
        # Create user
        user = auth_service.create_user(db, user_data.model_dump())
        
        # Log audit event
        log_audit_event(
            db=db,
            action=AuditAction.CREATE,
            resource_type="User",
            resource_id=str(user.id),
            user=None,
            request=request,
            description=f"New user registered: {user.email}"
        )
        
        return {
            "message": "User registered successfully",
            "user_id": user.user_id,
            "email": user.email,
            "username": user.username
        }
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Registration error: {str(e)}")  # Debug logging
        import traceback
        traceback.print_exc()  # Print full stack trace
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Registration failed: {str(e)}"
        )

@router.post("/login", response_model=TokenResponse)
async def login_user(
    login_data: UserLogin,
    request: Request,
    db: Session = Depends(get_database_session)
):
    """
    Login and get access tokens
    
    Authenticate user with email/username and password.
    Returns JWT tokens for API access.
    """
    try:
        # Authenticate user
        user = auth_service.authenticate_user(
            db=db,
            email_or_username=login_data.email_or_username,
            password=login_data.password,
            totp_code=login_data.totp_code
        )
        
        if not user:
            # Log failed login attempt
            log_audit_event(
                db=db,
                action=AuditAction.LOGIN,
                resource_type="User",
                resource_id="unknown",
                request=request,
                description=f"Failed login attempt for: {login_data.email_or_username}"
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid credentials"
            )
        
        # Create tokens
        tokens = auth_service.create_user_tokens(db, user)
        
        # Update last login
        user.last_login_at = datetime.utcnow()
        db.commit()
        
        # Log successful login
        log_audit_event(
            db=db,
            action=AuditAction.LOGIN,
            resource_type="User",
            resource_id=str(user.id),
            user=user,
            request=request,
            description="Successful login"
        )
        
        return TokenResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens["token_type"],
            expires_in=tokens["expires_in"],
            user_info=tokens["user_info"]
        )
    
    except HTTPException:
        raise
    except Exception as e:
        print(f"Login error: {str(e)}")  # Debug logging
        import traceback
        traceback.print_exc()  # Print full stack trace
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Login failed: {str(e)}"
        )

@router.post("/logout")
async def logout_user(
    request: Request,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Logout and invalidate tokens
    
    Logs out the current user and invalidates their session.
    """
    try:
        # Log logout event
        log_audit_event(
            db=db,
            action=AuditAction.LOGOUT,
            resource_type="User",
            resource_id=str(current_user.id),
            user=current_user,
            request=request,
            description="User logout"
        )
        
        # TODO: Invalidate tokens in session store/cache
        
        return {"message": "Logout successful"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Logout failed"
        )

@router.get("/me", response_model=UserProfile)
async def get_current_user_info(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user information
    
    Returns profile information for the authenticated user.
    """
    return UserProfile(
        id=str(current_user.id),
        user_id=current_user.user_id,
        email=current_user.email,
        username=current_user.username,
        first_name=current_user.first_name,
        last_name=current_user.last_name,
        role=current_user.role.value,
        two_factor_enabled=current_user.two_factor_enabled,
        is_active=current_user.is_active,
        created_at=current_user.created_at,
        last_login_at=current_user.last_login_at
    )

@router.post("/refresh")
async def refresh_token(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
):
    """
    Refresh access token
    
    Use refresh token to get a new access token.
    """
    try:
        # TODO: Implement refresh token logic
        # For now, return error
        raise HTTPException(
            status_code=status.HTTP_501_NOT_IMPLEMENTED,
            detail="Refresh token functionality not yet implemented"
        )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Token refresh failed"
        )

@router.post("/setup-2fa")
async def setup_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Setup two-factor authentication
    
    Generates TOTP secret and QR code for 2FA setup.
    """
    try:
        setup_data = auth_service.setup_2fa(db, current_user)
        
        # Log audit event
        log_audit_event(
            db=db,
            action=AuditAction.UPDATE,
            resource_type="User",
            resource_id=str(current_user.id),
            user=current_user,
            description="2FA setup initiated"
        )
        
        return {
            "message": "2FA setup initiated",
            "qr_code": setup_data["qr_code"],
            "secret": setup_data["secret"]
        }
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA setup failed"
        )

@router.post("/confirm-2fa")
async def confirm_2fa(
    setup_data: TwoFactorSetup,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Confirm two-factor authentication setup
    
    Verifies TOTP code and enables 2FA for the user.
    """
    try:
        success = auth_service.confirm_2fa_setup(db, current_user, setup_data.totp_code)
        
        if success:
            # Log audit event
            log_audit_event(
                db=db,
                action=AuditAction.UPDATE,
                resource_type="User",
                resource_id=str(current_user.id),
                user=current_user,
                description="2FA enabled successfully"
            )
            
            return {"message": "2FA enabled successfully"}
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid 2FA code"
            )
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA confirmation failed"
        )

@router.post("/disable-2fa")
async def disable_2fa(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Disable two-factor authentication
    
    Disables 2FA for the current user.
    """
    try:
        current_user.two_factor_enabled = False
        current_user.totp_secret = None
        db.commit()
        
        # Log audit event
        log_audit_event(
            db=db,
            action=AuditAction.UPDATE,
            resource_type="User",
            resource_id=str(current_user.id),
            user=current_user,
            description="2FA disabled"
        )
        
        return {"message": "2FA disabled successfully"}
    
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="2FA disable failed"
        )

@router.post("/change-password")
async def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_database_session)
):
    """
    Change user password
    
    Updates the user's password after verifying current password.
    """
    try:
        # Verify current password
        if not security_service.verify_password(password_data.current_password, current_user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Current password is incorrect"
            )
        
        # Update password
        current_user.hashed_password = security_service.hash_password(password_data.new_password)
        db.commit()
        
        # Log audit event
        log_audit_event(
            db=db,
            action=AuditAction.UPDATE,
            resource_type="User",
            resource_id=str(current_user.id),
            user=current_user,
            description="Password changed"
        )
        
        return {"message": "Password changed successfully"}
    
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Password change failed"
        )