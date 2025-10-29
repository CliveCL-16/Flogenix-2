"""
Enterprise Authentication and Security System
JWT-based authentication with role-based access control
"""

from datetime import datetime, timedelta, timezone
from typing import Optional, Dict, Any, List
from fastapi import HTTPException, status, Depends, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from passlib.context import CryptContext
from jose import JWTError, jwt
from pydantic import BaseModel, EmailStr
import secrets
import pyotp
import qrcode
import io
import base64

from app.core.config import get_settings
from app.core.database import get_database_session
from app.models import UserInfo
from app.core.models import User, UserSession, UserRole, AuditLog, AuditAction

# Security setup - Using pbkdf2_sha256 as fallback due to bcrypt version issues
pwd_context = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
security = HTTPBearer()
settings = get_settings()

# Pydantic models
class UserCreate(BaseModel):
    email: EmailStr
    username: str
    password: str
    first_name: str
    last_name: str
    phone_number: Optional[str] = None
    role: UserRole = UserRole.USER

class UserUpdate(BaseModel):
    email: Optional[EmailStr] = None
    username: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    phone_number: Optional[str] = None
    is_active: Optional[bool] = None

class UserLogin(BaseModel):
    email_or_username: str
    password: str
    totp_code: Optional[str] = None

class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in: int
    user_info: Dict[str, Any]

class PasswordReset(BaseModel):
    email: EmailStr

class PasswordResetConfirm(BaseModel):
    token: str
    new_password: str

class PasswordChange(BaseModel):
    current_password: str
    new_password: str

class TwoFactorSetup(BaseModel):
    totp_code: str

class SecurityService:
    """Handles authentication, authorization, and security operations"""
    
    def __init__(self):
        self.settings = get_settings()
    
    def hash_password(self, password: str) -> str:
        """Hash a password using pbkdf2_sha256"""
        return pwd_context.hash(password)
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """Verify a password against its hash"""
        return pwd_context.verify(plain_password, hashed_password)
    
    def validate_password_strength(self, password: str) -> List[str]:
        """Validate password meets security requirements"""
        errors = []
        
        if len(password) < self.settings.security.min_password_length:
            errors.append(f"Password must be at least {self.settings.security.min_password_length} characters long")
        
        if self.settings.security.require_uppercase and not any(c.isupper() for c in password):
            errors.append("Password must contain at least one uppercase letter")
        
        if self.settings.security.require_numbers and not any(c.isdigit() for c in password):
            errors.append("Password must contain at least one number")
        
        if self.settings.security.require_special_chars and not any(c in "!@#$%^&*()_+-=[]{}|;:,.<>?" for c in password):
            errors.append("Password must contain at least one special character")
        
        return errors
    
    def create_access_token(self, data: Dict[str, Any], expires_delta: Optional[timedelta] = None) -> str:
        """Create JWT access token"""
        to_encode = data.copy()
        
        if expires_delta:
            expire = datetime.now(timezone.utc) + expires_delta
        else:
            expire = datetime.now(timezone.utc) + timedelta(minutes=self.settings.security.access_token_expire_minutes)
        
        to_encode.update({"exp": expire, "type": "access"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.security.secret_key,
            algorithm=self.settings.security.algorithm
        )
        
        return encoded_jwt
    
    def create_refresh_token(self, data: Dict[str, Any]) -> str:
        """Create JWT refresh token"""
        to_encode = data.copy()
        expire = datetime.now(timezone.utc) + timedelta(days=self.settings.security.refresh_token_expire_days)
        
        to_encode.update({"exp": expire, "type": "refresh"})
        
        encoded_jwt = jwt.encode(
            to_encode,
            self.settings.security.secret_key,
            algorithm=self.settings.security.algorithm
        )
        
        return encoded_jwt
    
    def verify_token(self, token: str, token_type: str = "access") -> Dict[str, Any]:
        """Verify and decode JWT token"""
        try:
            payload = jwt.decode(
                token,
                self.settings.security.secret_key,
                algorithms=[self.settings.security.algorithm]
            )
            
            # Check token type
            if payload.get("type") != token_type:
                raise JWTError("Invalid token type")
            
            return payload
            
        except JWTError:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token",
                headers={"WWW-Authenticate": "Bearer"},
            )
    
    def generate_2fa_secret(self) -> str:
        """Generate a new 2FA secret"""
        return pyotp.random_base32()
    
    def generate_2fa_qr_code(self, user_email: str, secret: str) -> str:
        """Generate QR code for 2FA setup"""
        totp_uri = pyotp.totp.TOTP(secret).provisioning_uri(
            name=user_email,
            issuer_name="Flogenix Enterprise"
        )
        
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(totp_uri)
        qr.make(fit=True)
        
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        # Convert to base64
        buffer = io.BytesIO()
        qr_img.save(buffer, format="PNG")
        qr_code_base64 = base64.b64encode(buffer.getvalue()).decode()
        
        return f"data:image/png;base64,{qr_code_base64}"
    
    def verify_2fa_code(self, secret: str, code: str) -> bool:
        """Verify TOTP code"""
        totp = pyotp.TOTP(secret)
        return totp.verify(code, valid_window=1)
    
    def check_user_locked(self, user: User) -> bool:
        """Check if user account is locked"""
        if user.locked_until and user.locked_until > datetime.utcnow():
            return True
        return False
    
    def lock_user_account(self, db: Session, user: User, duration_minutes: int = 30):
        """Lock user account for specified duration"""
        user.locked_until = datetime.utcnow() + timedelta(minutes=duration_minutes)
        user.failed_login_attempts = 0
        db.commit()
    
    def increment_failed_login(self, db: Session, user: User):
        """Increment failed login attempts and lock if threshold reached"""
        user.failed_login_attempts += 1
        
        if user.failed_login_attempts >= 5:  # Lock after 5 failed attempts
            self.lock_user_account(db, user, 30)  # Lock for 30 minutes
        
        db.commit()
    
    def reset_failed_login(self, db: Session, user: User):
        """Reset failed login attempts after successful login"""
        user.failed_login_attempts = 0
        user.locked_until = None
        user.last_login_at = datetime.utcnow()
        db.commit()

# Global security service instance
security_service = SecurityService()

class AuthService:
    """Main authentication service"""
    
    def __init__(self):
        self.security = security_service
    
    def create_user(self, db: Session, user_data: Dict[str, Any]) -> User:
        """Create a new user"""
        # Check if user already exists
        existing_user = db.query(User).filter(
            (User.email == user_data["email"]) | (User.username == user_data["username"])
        ).first()
        
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email or username already exists"
            )
        
        # Validate password strength
        password_errors = self.security.validate_password_strength(user_data["password"])
        if password_errors:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"password_errors": password_errors}
            )
        
        # Create user
        hashed_password = self.security.hash_password(user_data["password"])
        
        user = User(
            email=user_data["email"],
            username=user_data["username"],
            hashed_password=hashed_password,
            first_name=user_data["first_name"],
            last_name=user_data["last_name"],
            phone_number=user_data.get("phone_number"),
            role=user_data.get("role", UserRole.USER)
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return user
    
    def get_user_by_email_or_username(self, db: Session, email_or_username: str) -> Optional[User]:
        """Get user by email or username"""
        return db.query(User).filter(
            (User.email == email_or_username) | (User.username == email_or_username)
        ).first()
    
    def authenticate_user(self, db: Session, email_or_username: str, password: str, totp_code: Optional[str] = None) -> Optional[User]:
        """Authenticate user with email/username and password"""
        # Find user by email or username
        user = db.query(User).filter(
            (User.email == email_or_username) | (User.username == email_or_username)
        ).first()
        
        if not user:
            return None
        
        # Check if account is locked
        if self.security.check_user_locked(user):
            raise HTTPException(
                status_code=status.HTTP_423_LOCKED,
                detail="Account is temporarily locked due to too many failed login attempts"
            )
        
        # Check if user is active
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Account is deactivated"
            )
        
        # Verify password
        if not self.security.verify_password(password, user.hashed_password):
            self.security.increment_failed_login(db, user)
            return None
        
        # Check 2FA if enabled
        if user.two_factor_enabled:
            if not totp_code:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="2FA code required"
                )
            
            if not self.security.verify_2fa_code(user.two_factor_secret, totp_code):
                self.security.increment_failed_login(db, user)
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid 2FA code"
                )
        
        # Reset failed login attempts
        self.security.reset_failed_login(db, user)
        
        return user
    
    def create_user_tokens(self, db: Session, user: User) -> Dict[str, Any]:
        """Create access and refresh tokens for user"""
        # Create token data
        token_data = {
            "sub": str(user.id),
            "email": user.email,
            "role": user.role.value,
            "user_id": user.user_id
        }
        
        # Generate tokens
        access_token = self.security.create_access_token(token_data)
        refresh_token = self.security.create_refresh_token({"sub": str(user.id)})
        
        # Create session record
        session_id = secrets.token_urlsafe(32)
        expires_at = datetime.utcnow() + timedelta(days=self.security.settings.security.refresh_token_expire_days)
        
        user_session = UserSession(
            session_id=session_id,
            user_id=user.id,
            access_token=access_token,
            refresh_token=refresh_token,
            expires_at=expires_at
        )
        
        db.add(user_session)
        db.commit()
        
        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": self.security.settings.security.access_token_expire_minutes * 60,
            "user_info": {
                "id": user.id,
                "user_id": user.user_id,
                "email": user.email,
                "username": user.username,
                "first_name": user.first_name,
                "last_name": user.last_name,
                "role": user.role.value,
                "two_factor_enabled": user.two_factor_enabled
            }
        }
    
    def setup_2fa(self, db: Session, user: User) -> Dict[str, str]:
        """Setup 2FA for user"""
        secret = self.security.generate_2fa_secret()
        qr_code = self.security.generate_2fa_qr_code(user.email, secret)
        
        # Save secret (temporarily, until confirmed)
        user.two_factor_secret = secret
        db.commit()
        
        return {
            "secret": secret,
            "qr_code": qr_code
        }
    
    def confirm_2fa_setup(self, db: Session, user: User, totp_code: str) -> bool:
        """Confirm 2FA setup with TOTP code"""
        if not user.two_factor_secret:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="2FA setup not initiated"
            )
        
        if self.security.verify_2fa_code(user.two_factor_secret, totp_code):
            user.two_factor_enabled = True
            db.commit()
            return True
        
        return False
    
    def disable_2fa(self, db: Session, user: User, password: str) -> bool:
        """Disable 2FA for user"""
        if not self.security.verify_password(password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid password"
            )
        
        user.two_factor_enabled = False
        user.two_factor_secret = None
        db.commit()
        
        return True

# Global auth service instance
auth_service = AuthService()

# FastAPI dependencies
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_database_session)
) -> User:
    """Get current authenticated user"""
    try:
        # Verify token
        payload = security_service.verify_token(credentials.credentials)
        user_id = payload.get("sub")
        
        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid token"
            )
        
        # Get user from database
        user = db.query(User).filter(User.id == int(user_id)).first()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="User not found"
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Inactive user"
            )
        
        return user
        
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token",
            headers={"WWW-Authenticate": "Bearer"},
        )

def require_role(required_roles: List[UserRole]):
    """Require specific user roles"""
    def role_checker(current_user: User = Depends(get_current_user)) -> User:
        if current_user.role not in required_roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions"
            )
        return current_user
    
    return role_checker

# Role-specific dependencies
def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Require admin role"""
    if current_user.role not in [UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin access required"
        )
    return current_user

def require_processor(current_user: User = Depends(get_current_user)) -> User:
    """Require processor role or higher"""
    if current_user.role not in [UserRole.PROCESSOR, UserRole.ADMIN, UserRole.SUPER_ADMIN]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Processor access required"
        )
    return current_user

# Audit logging
def log_audit_event(
    db: Session,
    action: AuditAction,
    resource_type: str,
    resource_id: str,
    user: Optional[User] = None,
    request: Optional[Request] = None,
    old_values: Optional[Dict[str, Any]] = None,
    new_values: Optional[Dict[str, Any]] = None,
    description: Optional[str] = None
):
    """Log an audit event"""
    try:
        # Helper function to make data JSON serializable
        def make_json_serializable(data):
            if data is None:
                return None
            if isinstance(data, dict):
                return {k: make_json_serializable(v) for k, v in data.items()}
            elif isinstance(data, (list, tuple)):
                return [make_json_serializable(item) for item in data]
            elif isinstance(data, datetime):
                return data.isoformat()
            elif hasattr(data, '__dict__'):
                return str(data)
            else:
                return data
        
        audit_log = AuditLog(
            action=action,
            resource_type=resource_type,
            resource_id=resource_id,
            user_id=user.id if user else None,
            user_email=user.email if user else None,
            user_role=user.role.value if user else None,
            ip_address=request.client.host if request else None,
            user_agent=request.headers.get("user-agent") if request else None,
            request_method=request.method if request else None,
            request_path=str(request.url) if request else None,
            old_values=make_json_serializable(old_values),
            new_values=make_json_serializable(new_values),
            description=description
        )
        
        db.add(audit_log)
        db.commit()
        
    except Exception as e:
        # Don't let audit logging failures break the main operation
        print(f"Audit logging failed: {e}")
        db.rollback()


# WebSocket authentication
async def get_current_user_websocket(token: str, db: Session) -> Optional[UserInfo]:
    """Authenticate user for WebSocket connections"""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        email: str = payload.get("sub")
        if email is None:
            return None
    except JWTError:
        return None
    
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        return None
    
    # Convert to UserInfo for WebSocket
    return UserInfo(
        id=user.id,
        user_id=user.user_id,
        email=user.email,
        username=user.username,
        first_name=user.first_name,
        last_name=user.last_name,
        role=user.role.value,
        two_factor_enabled=user.two_factor_enabled
    )