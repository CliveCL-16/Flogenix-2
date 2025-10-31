"""
Enterprise Configuration Management
Centralized configuration for the Flogenix enterprise backend
"""

from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Optional, List
import os
from pathlib import Path

class DatabaseSettings(BaseSettings):
    """Database configuration"""
    url: str = Field(default="sqlite:///./flogenix_enterprise.db", env="DATABASE_URL")
    echo: bool = Field(default=False, env="DATABASE_ECHO")
    pool_size: int = Field(default=20, env="DATABASE_POOL_SIZE")
    max_overflow: int = Field(default=30, env="DATABASE_MAX_OVERFLOW")
    
class SecuritySettings(BaseSettings):
    """Security and authentication configuration"""
    secret_key: str = Field(default="flogenix-super-secret-key-change-in-production", env="SECRET_KEY")
    algorithm: str = Field(default="HS256", env="JWT_ALGORITHM")
    access_token_expire_minutes: int = Field(default=30, env="ACCESS_TOKEN_EXPIRE_MINUTES")
    refresh_token_expire_days: int = Field(default=7, env="REFRESH_TOKEN_EXPIRE_DAYS")
    
    # Password requirements
    min_password_length: int = Field(default=8, env="MIN_PASSWORD_LENGTH")
    require_uppercase: bool = Field(default=True, env="REQUIRE_UPPERCASE")
    require_numbers: bool = Field(default=True, env="REQUIRE_NUMBERS")
    require_special_chars: bool = Field(default=True, env="REQUIRE_SPECIAL_CHARS")

class AISettings(BaseSettings):
    """AI and ML configuration"""
    # Gemini API configuration
    gemini_api_key: Optional[str] = Field(default=None, env="GEMINI_API_KEY")
    gemini_model: str = Field(default="gemini-2.5-flash", env="GEMINI_MODEL")
    gemini_temperature: float = Field(default=0.1, env="GEMINI_TEMPERATURE")
    max_tokens: int = Field(default=2000, env="GEMINI_MAX_TOKENS")
    
    # Legacy OpenAI support (for migration)
    openai_api_key: Optional[str] = Field(default=None, env="OPENAI_API_KEY")
    openai_model: str = Field(default="gpt-4", env="OPENAI_MODEL")
    openai_temperature: float = Field(default=0.1, env="OPENAI_TEMPERATURE")
    
    # Agent configuration
    max_agent_processing_time: int = Field(default=300, env="MAX_AGENT_PROCESSING_TIME")  # seconds
    agent_retry_attempts: int = Field(default=3, env="AGENT_RETRY_ATTEMPTS")
    
    # Advanced AI features
    enable_autonomous_exceptions: bool = Field(default=True, env="ENABLE_AUTONOMOUS_EXCEPTIONS")
    enable_continuous_learning: bool = Field(default=True, env="ENABLE_CONTINUOUS_LEARNING")
    enable_dynamic_triage: bool = Field(default=True, env="ENABLE_DYNAMIC_TRIAGE")
    enable_predictive_fraud: bool = Field(default=True, env="ENABLE_PREDICTIVE_FRAUD")
    enable_ai_customer_support: bool = Field(default=True, env="ENABLE_AI_CUSTOMER_SUPPORT")
    enable_human_in_loop: bool = Field(default=True, env="ENABLE_HUMAN_IN_LOOP")
    
class RedisSettings(BaseSettings):
    """Redis configuration for caching and async processing"""
    url: str = Field(default="redis://localhost:6379/0", env="REDIS_URL")
    max_connections: int = Field(default=20, env="REDIS_MAX_CONNECTIONS")
    socket_timeout: int = Field(default=30, env="REDIS_SOCKET_TIMEOUT")

class CelerySettings(BaseSettings):
    """Celery configuration for async task processing"""
    broker_url: str = Field(default="redis://localhost:6379/1", env="CELERY_BROKER_URL")
    result_backend: str = Field(default="redis://localhost:6379/2", env="CELERY_RESULT_BACKEND")
    task_serializer: str = Field(default="json", env="CELERY_TASK_SERIALIZER")
    result_serializer: str = Field(default="json", env="CELERY_RESULT_SERIALIZER")
    accept_content: List[str] = Field(default=["json"], env="CELERY_ACCEPT_CONTENT")
    timezone: str = Field(default="UTC", env="CELERY_TIMEZONE")

class APISettings(BaseSettings):
    """API configuration"""
    cors_origins: List[str] = Field(
        default=[
            "http://localhost:3000",
            "http://127.0.0.1:3000",
            "http://localhost:5173",
            "http://127.0.0.1:5173",
            "http://localhost:8080",
            "http://127.0.0.1:8080",
            "http://localhost:8501",
            "http://127.0.0.1:8501"
        ],
        env="CORS_ORIGINS"
    )
    max_request_size: int = Field(default=10 * 1024 * 1024, env="MAX_REQUEST_SIZE")  # 10MB
    rate_limit_per_minute: int = Field(default=100, env="RATE_LIMIT_PER_MINUTE")

class LoggingSettings(BaseSettings):
    """Logging configuration"""
    level: str = Field(default="INFO", env="LOG_LEVEL")
    format: str = Field(default="json", env="LOG_FORMAT")  # json or text
    file_path: Optional[str] = Field(default=None, env="LOG_FILE_PATH")
    max_file_size: int = Field(default=10 * 1024 * 1024, env="LOG_MAX_FILE_SIZE")  # 10MB
    backup_count: int = Field(default=5, env="LOG_BACKUP_COUNT")

class MonitoringSettings(BaseSettings):
    """Monitoring and metrics configuration"""
    enable_metrics: bool = Field(default=True, env="ENABLE_METRICS")
    metrics_port: int = Field(default=8001, env="METRICS_PORT")
    health_check_interval: int = Field(default=30, env="HEALTH_CHECK_INTERVAL")  # seconds

class EnterpriseSettings(BaseSettings):
    """Main enterprise settings"""
    app_name: str = Field(default="Flogenix Enterprise", env="APP_NAME")
    version: str = Field(default="2.0.0", env="APP_VERSION")
    debug: bool = Field(default=False, env="DEBUG")
    environment: str = Field(default="development", env="ENVIRONMENT")  # development, staging, production
    
    # Feature flags
    enable_audit_logs: bool = Field(default=True, env="ENABLE_AUDIT_LOGS")
    enable_2fa: bool = Field(default=True, env="ENABLE_2FA")
    enable_real_time_processing: bool = Field(default=True, env="ENABLE_REAL_TIME_PROCESSING")
    enable_fraud_detection: bool = Field(default=True, env="ENABLE_FRAUD_DETECTION")
    
    # File upload settings
    max_file_size: int = Field(default=50 * 1024 * 1024, env="MAX_FILE_SIZE")  # 50MB
    allowed_file_types: List[str] = Field(
        default=["pdf", "jpg", "jpeg", "png", "doc", "docx"],
        env="ALLOWED_FILE_TYPES"
    )
    
    # Compliance settings
    data_retention_days: int = Field(default=2555, env="DATA_RETENTION_DAYS")  # 7 years
    audit_retention_days: int = Field(default=2555, env="AUDIT_RETENTION_DAYS")  # 7 years
    
    # Nested settings
    database: DatabaseSettings = DatabaseSettings()
    security: SecuritySettings = SecuritySettings()
    ai: AISettings = AISettings()
    redis: RedisSettings = RedisSettings()
    celery: CelerySettings = CelerySettings()
    api: APISettings = APISettings()
    logging: LoggingSettings = LoggingSettings()
    monitoring: MonitoringSettings = MonitoringSettings()
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
        extra = "ignore"  # Allow extra fields to be ignored

# Global settings instance
settings = EnterpriseSettings()

def get_settings() -> EnterpriseSettings:
    """Get application settings"""
    return settings

def is_production() -> bool:
    """Check if running in production environment"""
    return settings.environment.lower() == "production"

def is_development() -> bool:
    """Check if running in development environment"""
    return settings.environment.lower() == "development"