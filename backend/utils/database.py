import logging
import os

from models.base import Base
from sqlalchemy.ext.asyncio import AsyncEngine, AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

logger = logging.getLogger(__name__)


class Database:
    def __init__(self):
        try:
            logger.info("Initializing database connection")
            self.DATABASE_URL = os.getenv("DATABASE_URL")
            self.DATABASE_ASYNC_URL = os.getenv("DATABASE_ASYNC_URL")

            if not self.DATABASE_URL or not self.DATABASE_ASYNC_URL:
                logger.error("Database URLs not found in environment variables")
                raise ValueError("Database URLs not configured")

            logger.debug(f"Creating async engine with URL: {self.DATABASE_ASYNC_URL}")
            self.engine: AsyncEngine = create_async_engine(
                self.DATABASE_ASYNC_URL, echo=True, future=True
            )

            self.async_session = sessionmaker(
                self.engine, class_=AsyncSession, expire_on_commit=False
            )
            logger.info("Database connection initialized successfully")

        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}", exc_info=True)
            raise

    async def get_session(self) -> AsyncSession:
        """Get a database session."""
        try:
            logger.debug("Creating new database session")
            async with self.async_session() as session:
                yield session
                logger.debug("Database session closed")
        except Exception as e:
            logger.error(f"Error in database session: {str(e)}", exc_info=True)
            raise

    def get_db_url(self) -> str:
        """Get the synchronous database URL."""
        return self.DATABASE_URL


# Make the database session available as a dependency
async def get_db():
    """Database session dependency."""
    db = Database()
    try:
        logger.debug("Starting database session")
        async for session in db.get_session():
            try:
                yield session
            except Exception as e:
                logger.error(f"Error during database session: {str(e)}", exc_info=True)
                await session.rollback()
                raise
            finally:
                logger.debug("Closing database session")
                await session.close()
    except Exception as e:
        logger.error(f"Failed to get database session: {str(e)}", exc_info=True)
        raise
