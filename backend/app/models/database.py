from sqlalchemy import create_engine, Column, Integer, String, DateTime, Float, Text, Boolean, Date, ForeignKey, JSON
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

Base = declarative_base()

# Database engine and session
DATABASE_URL = "sqlite:///./flogenix.db"
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 1. Claim - Main claims table
class Claim(Base):
    __tablename__ = 'claims'

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(20), unique=True, index=True)
    patient_name = Column(String(100))
    patient_id = Column(String(50), index=True)
    insurance_provider = Column(String(100))
    policy_number = Column(String(50))
    diagnosis_code = Column(String(10), index=True)
    procedure_code = Column(String(10), index=True)
    claim_amount = Column(Float)
    service_date = Column(Date)
    provider_name = Column(String(100), index=True)
    provider_npi = Column(String(10))
    status = Column(String(20), index=True)  # APPROVED, DENIED, PENDING_REVIEW, FRAUD_FLAGGED
    created_at = Column(DateTime, default=datetime.utcnow)
    processed_at = Column(DateTime, nullable=True)
    notes = Column(Text, nullable=True)

    # Relationships
    decision_logs = relationship("DecisionLog", back_populates="claim")
    fraud_analyses = relationship("FraudAnalysis", back_populates="claim")
    exception_logs = relationship("ExceptionLog", back_populates="claim")
    claim_features = relationship("ClaimFeatures", back_populates="claim", uselist=False)

# 2. DecisionLog - AI decision records
class DecisionLog(Base):
    __tablename__ = 'decision_logs'

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(20), ForeignKey('claims.claim_id'), index=True)
    decision = Column(String(20))  # APPROVE, DENY, REVIEW
    confidence_score = Column(Float)  # 0-100
    reasoning_text = Column(Text)
    fraud_score = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    agent_reports = Column(JSON, nullable=True)  # Store detailed agent analysis

    # Relationship
    claim = relationship("Claim", back_populates="decision_logs")

# 3. FraudAnalysis - Fraud detection results
class FraudAnalysis(Base):
    __tablename__ = 'fraud_analysis'

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(20), ForeignKey('claims.claim_id'), index=True)
    fraud_score = Column(Float)  # 0-100
    risk_factors = Column(JSON)  # List of risk factors
    is_flagged = Column(Boolean, default=False)
    analysis_details = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    claim = relationship("Claim", back_populates="fraud_analyses")

# 4. ExceptionLog - Exception handling records
class ExceptionLog(Base):
    __tablename__ = 'exception_logs'

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(20), ForeignKey('claims.claim_id'), index=True)
    exception_type = Column(String(50), index=True)
    resolution_action = Column(Text)
    learned_from_case_id = Column(String(20), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    claim = relationship("Claim", back_populates="exception_logs")

# 5. ProviderAnalytics - Provider performance tracking
class ProviderAnalytics(Base):
    __tablename__ = 'provider_analytics'

    id = Column(Integer, primary_key=True, index=True)
    provider_name = Column(String(100), unique=True, index=True)
    provider_npi = Column(String(10), index=True, nullable=True)
    total_claims = Column(Integer, default=0)
    approved_claims = Column(Integer, default=0)
    denied_claims = Column(Integer, default=0)
    fraud_flagged_claims = Column(Integer, default=0)
    total_amount = Column(Float, default=0.0)
    approval_rate = Column(Float, nullable=True)
    avg_processing_time = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

# 6. DiagnosisPatterns - Medical code analytics
class DiagnosisPatterns(Base):
    __tablename__ = 'diagnosis_patterns'

    id = Column(Integer, primary_key=True, index=True)
    diagnosis_code = Column(String(10), unique=True, index=True)
    description = Column(String(200))
    frequency = Column(Integer, default=0)
    avg_claim_amount = Column(Float, nullable=True)
    common_procedures = Column(JSON, nullable=True)  # Top 5 associated procedures
    approval_rate = Column(Float, nullable=True)
    fraud_rate = Column(Float, nullable=True)
    last_updated = Column(DateTime, default=datetime.utcnow)

# 7. ClaimFeatures - ML training data
class ClaimFeatures(Base):
    __tablename__ = 'claim_features'

    id = Column(Integer, primary_key=True, index=True)
    claim_id = Column(String(20), ForeignKey('claims.claim_id'), index=True)
    # Normalized features for ML
    amount_zscore = Column(Float, nullable=True)  # Z-score of claim amount
    provider_claim_frequency = Column(Float, nullable=True)  # Claims per day
    diagnosis_frequency = Column(Float, nullable=True)  # How common is this diagnosis
    procedure_complexity = Column(Float, nullable=True)  # Procedure complexity score
    temporal_anomaly = Column(Float, nullable=True)  # Time-based anomaly score
    fraud_label = Column(Integer, nullable=True)  # 0=legit, 1=fraud (for training)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationship
    claim = relationship("Claim", back_populates="claim_features")

# 8. SystemMetrics - Performance tracking
class SystemMetrics(Base):
    __tablename__ = 'system_metrics'

    id = Column(Integer, primary_key=True, index=True)
    date = Column(Date, index=True)
    total_claims_processed = Column(Integer, default=0)
    avg_processing_time = Column(Float, nullable=True)
    approval_rate = Column(Float, nullable=True)
    fraud_detection_rate = Column(Float, nullable=True)
    agent_performance = Column(JSON, nullable=True)  # Performance of each agent
    created_at = Column(DateTime, default=datetime.utcnow)

# Create all tables
def create_tables():
    """Create all database tables"""
    Base.metadata.create_all(bind=engine)

# Dependency to get database session
def get_db():
    """Get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

if __name__ == "__main__":
    create_tables()
    print("Database tables created successfully!")