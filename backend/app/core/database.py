"""
Enterprise Database Setup and Connection Management
"""

from sqlalchemy import create_engine, event
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from app.core.config import get_settings
import logging

logger = logging.getLogger(__name__)

class DatabaseManager:
    """Manages database connections and sessions"""
    
    def __init__(self):
        self.settings = get_settings()
        self._engine = None
        self._session_factory = None
        
    @property
    def engine(self):
        """Get or create database engine"""
        if self._engine is None:
            self._engine = self._create_engine()
        return self._engine
    
    @property
    def session_factory(self):
        """Get or create session factory"""
        if self._session_factory is None:
            self._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=self.engine
            )
        return self._session_factory
    
    def _create_engine(self):
        """Create database engine with appropriate configuration"""
        database_url = self.settings.database.url

        try:
            if database_url.startswith("sqlite"):
                # SQLite configuration
                engine = create_engine(
                    database_url,
                    echo=self.settings.database.echo,
                    poolclass=StaticPool,
                    connect_args={
                        "check_same_thread": False,
                        "timeout": 30,
                        "isolation_level": None
                    }
                )

                # Enable foreign keys for SQLite
                @event.listens_for(engine, "connect")
                def set_sqlite_pragma(dbapi_connection, connection_record):
                    cursor = dbapi_connection.cursor()
                    cursor.execute("PRAGMA foreign_keys=ON")
                    cursor.execute("PRAGMA journal_mode=WAL")
                    cursor.execute("PRAGMA synchronous=NORMAL")
                    cursor.execute("PRAGMA cache_size=1000")
                    cursor.execute("PRAGMA temp_store=memory")
                    cursor.close()

            else:
                # PostgreSQL configuration
                engine = create_engine(
                    database_url,
                    echo=self.settings.database.echo,
                    pool_size=self.settings.database.pool_size,
                    max_overflow=self.settings.database.max_overflow,
                    pool_pre_ping=True,
                    pool_recycle=3600,  # Recycle connections every hour
                    connect_args={
                        "application_name": "Flogenix Enterprise",
                        "options": "-c timezone=UTC"
                    }
                )

            # Test the connection
            with engine.connect() as conn:
                conn.execute("SELECT 1")

            logger.info(f"Created database engine for: {database_url}")
            return engine

        except Exception as e:
            logger.error(f"Failed to create database engine: {e}")
            logger.error(f"Database URL: {database_url}")
            raise
    
    def create_tables(self):
        """Create all database tables"""
        try:
            Base.metadata.create_all(bind=self.engine)
            logger.info("Database tables created successfully")
        except Exception as e:
            logger.error(f"Failed to create database tables: {e}")
            logger.error(f"Engine: {self._engine}")
            logger.error(f"Database URL: {self.settings.database.url}")
            raise
    
    def get_session(self) -> Session:
        """Get a new database session"""
        return self.session_factory()
    
    def close(self):
        """Close database connections"""
        if self._engine:
            self._engine.dispose()
            logger.info("Database engine disposed")

# Global database manager instance
db_manager = DatabaseManager()

# Create Base for enterprise models
Base = declarative_base()

def get_database_session():
    """FastAPI dependency for getting database sessions"""
    session = db_manager.get_session()
    try:
        yield session
    except Exception as e:
        session.rollback()
        logger.error(f"Database session error: {e}")
        logger.error(f"Session details - Engine: {db_manager._engine}, URL: {db_manager.settings.database.url}")
        logger.error(f"Exception type: {type(e).__name__}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        raise
    finally:
        session.close()

def init_database():
    """Initialize database tables"""
    try:
        # Ensure engine is created
        if db_manager._engine is None:
            db_manager._engine = db_manager._create_engine()

        # Ensure session factory is created
        if db_manager._session_factory is None:
            db_manager._session_factory = sessionmaker(
                autocommit=False,
                autoflush=False,
                bind=db_manager.engine
            )

        db_manager.create_tables()
        logger.info("Database initialized successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        logger.error(f"Database URL: {db_manager.settings.database.url}")
        logger.error(f"Engine created: {db_manager._engine is not None}")
        import traceback
        logger.error(f"Traceback: {traceback.format_exc()}")
        return False

def get_db():
    """Alternative FastAPI dependency for database sessions"""
    return get_database_session()

# Health check functions
def check_database_health() -> dict:
    """Check database connectivity and health"""
    try:
        session = db_manager.get_session()

        # Test basic connectivity
        session.execute("SELECT 1")

        # Get basic stats
        from app.core.models import User, Claim

        user_count = session.query(User).count()
        claim_count = session.query(Claim).count()

        session.close()

        return {
            "status": "healthy",
            "database_url": db_manager.settings.database.url.split("@")[-1] if "@" in db_manager.settings.database.url else db_manager.settings.database.url,
            "user_count": user_count,
            "claim_count": claim_count,
            "engine_info": {
                "pool_size": db_manager.settings.database.pool_size,
                "max_overflow": db_manager.settings.database.max_overflow
            }
        }

    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        logger.error(f"Database URL: {db_manager.settings.database.url}")
        logger.error(f"Engine created: {db_manager._engine is not None}")
        return {
            "status": "unhealthy",
            "error": str(e),
            "database_url": db_manager.settings.database.url if hasattr(db_manager, 'settings') else "unknown"
        }

def close_database():
    """Close database connections (for cleanup)"""
    db_manager.close()