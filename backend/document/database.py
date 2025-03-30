from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from sqlalchemy.ext.asyncio import AsyncEngine
import os
from models.base import Base


class Database:
    def __init__(self):
        self.DATABASE_URL = os.getenv("DATABASE_URL")
        self.DATABASE_ASYNC_URL = os.getenv("DATABASE_ASYNC_URL")
        self.engine: AsyncEngine = create_async_engine(
            self.DATABASE_ASYNC_URL, echo=True, future=True
        )

        self.async_session = sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_session(self) -> AsyncSession:
        async with self.async_session() as session:
            yield session

    def get_db_url(self):
        return self.DATABASE_URL
