import os
import logging
from sqlalchemy import create_engine, text as sqlalchemy_text
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.ext.declarative import declarative_base
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Get database URL from environment variables
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    logging.warning("No DATABASE_URL found. Using SQLite database.")
    DATABASE_URL = "sqlite:///announcements.db"

# Create database engine with SSL handling
if "postgresql" in DATABASE_URL:
    engine = create_engine(
        DATABASE_URL,
        pool_pre_ping=True,  # Check connection before using
        pool_recycle=3600,   # Recycle connections every hour
        connect_args={
            "sslmode": "require",
            "connect_timeout": 10
        }
    )
else:
    engine = create_engine(DATABASE_URL)

# Create session factory
SessionFactory = sessionmaker(bind=engine)
Session = scoped_session(SessionFactory)

# Create base class for models
Base = declarative_base()

def init_db():
    """Initialize the database and create tables."""
    # Import models to ensure they're registered with the Base
    import models
    
    global engine, SessionFactory, Session
    
    try:
        # Create tables if they don't exist
        Base.metadata.create_all(engine)
        logging.info("Database tables created.")
    except Exception as e:
        logging.warning(f"Error creating tables: {e}")
        logging.info("Tables may already exist, continuing...")
    
    # Check if we can connect to the database
    try:
        session = get_session()
        session.execute(sqlalchemy_text("SELECT 1"))
        session.close()
        logging.info("Database connection successful.")
    except Exception as e:
        logging.error(f"Database connection error: {e}")
        logging.warning("Using SQLite fallback if PostgreSQL fails.")
        # If connecting to PostgreSQL fails, set up SQLite fallback
        engine = create_engine("sqlite:///announcements.db")
        SessionFactory = sessionmaker(bind=engine)
        Session = scoped_session(SessionFactory)
        Base.metadata.create_all(engine)
        logging.info("Created SQLite database as fallback.")


# SQLAlchemy text function is imported at the top of the file

def get_session():
    """Get a database session with error handling."""
    global engine, SessionFactory, Session
    
    try:
        # Try to get a session with retries for intermittent connection issues
        session = Session()
        # Test the connection works
        session.execute(sqlalchemy_text("SELECT 1"))
        return session
    except Exception as e:
        # If we get a connection error, log it and create a new engine/session
        logging.error(f"Database connection error in get_session: {e}")
        logging.info("Attempting to reconnect to database...")
        
        try:
            # Close all existing connections
            Session.remove()
            
            # Recreate the engine with a new connection pool
            if "postgresql" in DATABASE_URL:
                engine = create_engine(
                    DATABASE_URL,
                    pool_pre_ping=True,  # Check connection before using
                    pool_recycle=3600,   # Recycle connections every hour
                    connect_args={
                        "sslmode": "require",
                        "connect_timeout": 10
                    },
                    pool_size=5,  # Use a smaller pool size
                    max_overflow=10
                )
            else:
                engine = create_engine(DATABASE_URL)
                
            # Recreate session factory with new engine
            SessionFactory = sessionmaker(bind=engine)
            Session = scoped_session(SessionFactory)
            
            # Try getting a new session
            new_session = Session()
            new_session.execute(sqlalchemy_text("SELECT 1"))
            logging.info("Successfully reconnected to database")
            return new_session
        except Exception as retry_error:
            logging.error(f"Failed to reconnect to database: {retry_error}")
            logging.warning("Using SQLite fallback database")
            
            # Switch to SQLite fallback
            engine = create_engine("sqlite:///announcements.db")
            Base.metadata.create_all(engine)  # Create tables if they don't exist
            SessionFactory = sessionmaker(bind=engine)
            Session = scoped_session(SessionFactory)
            return Session()
