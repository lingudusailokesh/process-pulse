import os
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.core.config import settings

logger = logging.getLogger("process_pulse.db")

def get_engine():
    """
    Initializes the database engine.
    Tries MySQL according to settings, with transparent SQLite fallback
    for frictionless local offline development/testing.
    """
    db_url = settings.get_database_url
    
    # Check if SQLite or MySQL
    if "sqlite" in db_url:
        return create_engine(db_url, connect_args={"check_same_thread": False})
    
    try:
        engine = create_engine(
            db_url,
            pool_pre_ping=True,
            pool_recycle=3600,
            pool_size=10,
            max_overflow=20
        )
        # Test connection
        with engine.connect() as conn:
            pass
        logger.info("Successfully connected to MySQL database.")
        return engine
    except Exception as e:
        logger.warning(f"MySQL connection to {db_url} failed: {e}. Falling back to SQLite local database.")
        db_file = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), "process_pulse.db")
        sqlite_fallback = f"sqlite:///{db_file}"
        return create_engine(sqlite_fallback, connect_args={"check_same_thread": False})

engine = get_engine()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def get_db():
    """FastAPI Dependency for database session injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
