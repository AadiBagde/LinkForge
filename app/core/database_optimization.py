"""
Database optimization and connection pooling configuration.
"""

from sqlalchemy import create_engine, event
from sqlalchemy.pool import QueuePool, NullPool
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


def get_engine_config(database_url: str):
    """
    Get optimized engine configuration based on database type and environment.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        Dictionary of engine configuration parameters
    """
    
    config = {}
    
    # Determine if PostgreSQL or MySQL
    is_postgres = database_url.startswith("postgresql")
    is_mysql = database_url.startswith("mysql")
    
    # Base configuration for all databases
    config["echo"] = settings.DEBUG
    config["pool_pre_ping"] = True  # Verify connections before using
    config["pool_recycle"] = 3600  # Recycle connections after 1 hour
    
    if settings.DEBUG:
        # Development: Simpler pooling
        config["poolclass"] = QueuePool
        config["pool_size"] = 5
        config["max_overflow"] = 10
        config["pool_timeout"] = 30
    else:
        # Production: More robust pooling
        config["poolclass"] = QueuePool
        config["pool_size"] = 20  # Number of connections to keep in pool
        config["max_overflow"] = 40  # Additional connections allowed
        config["pool_timeout"] = 30
        config["connect_args"] = {
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
        }
    
    if is_postgres:
        # PostgreSQL-specific optimizations
        config["connect_args"] = {
            "connect_timeout": 10,
            "keepalives": 1,
            "keepalives_idle": 30,
            "keepalives_interval": 10,
            "keepalives_count": 5,
            "options": "-c statement_timeout=30000"  # 30 second statement timeout
        }
    
    elif is_mysql:
        # MySQL-specific optimizations
        config["connect_args"] = {
            "connect_timeout": 10,
            "charset": "utf8mb4",
            "autocommit": True,
        }
    
    return config


def setup_database_event_listeners(engine):
    """
    Setup event listeners for database optimizations.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    
    @event.listens_for(engine, "connect")
    def receive_connect(dbapi_conn, connection_record):
        """Configure connection when created."""
        logger.debug("Database connection established")
        
        # Check if PostgreSQL
        if hasattr(dbapi_conn, 'set_isolation_level'):
            # PostgreSQL connection
            try:
                dbapi_conn.set_isolation_level(1)  # READ_COMMITTED
            except Exception as e:
                logger.warning(f"Failed to set PostgreSQL isolation level: {e}")
    
    @event.listens_for(engine, "pool_connect")
    def receive_pool_connect(dbapi_conn, connection_record):
        """Configure connection from pool."""
        logger.debug("Connection retrieved from pool")
    
    @event.listens_for(engine, "pool_invalidate")
    def receive_pool_invalidate(dbapi_conn, connection_record, exception):
        """Handle pool invalidation."""
        logger.warning(f"Connection invalidated due to: {exception}")
    
    @event.listens_for(engine, "pool_detach")
    def receive_pool_detach(dbapi_conn, connection_record):
        """Handle connection detachment."""
        logger.debug("Connection detached from pool")


def create_optimized_engine(database_url: str):
    """
    Create an optimized SQLAlchemy engine.
    
    Args:
        database_url: Database connection URL
        
    Returns:
        Configured SQLAlchemy engine
    """
    
    config = get_engine_config(database_url)
    logger.info(f"Creating database engine with config: {config}")
    
    engine = create_engine(database_url, **config)
    setup_database_event_listeners(engine)
    
    logger.info("Database engine created and configured")
    return engine


# Database migration utilities
def run_migrations():
    """
    Run Alembic migrations to sync database schema.
    
    This should be called during application startup if AUTO_MIGRATE is enabled.
    """
    from alembic.config import Config
    from alembic.command import upgrade
    
    try:
        alembic_cfg = Config("alembic.ini")
        upgrade(alembic_cfg, "head")
        logger.info("Database migrations completed successfully")
    except Exception as e:
        logger.error(f"Database migration failed: {e}")
        raise


def check_database_health(engine):
    """
    Check database connection health.
    
    Args:
        engine: SQLAlchemy engine instance
        
    Returns:
        Boolean indicating if database is healthy
    """
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        logger.info("Database health check passed")
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


# Migration helper functions
def backup_database(database_url: str, backup_path: str):
    """
    Create a backup of the database.
    
    Note: This is a placeholder. Actual implementation depends on database type.
    
    Args:
        database_url: Database connection URL
        backup_path: Path to save backup
    """
    logger.warning("Backup functionality not yet implemented")


def optimize_database_indexes(engine):
    """
    Optimize database indexes.
    
    Note: Database should be stopped before running this in production.
    
    Args:
        engine: SQLAlchemy engine instance
    """
    logger.info("Index optimization placeholder - run database-specific commands manually")
    # PostgreSQL: REINDEX;
    # MySQL: OPTIMIZE TABLE urls, clicks, users;
