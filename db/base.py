from sqlalchemy import MetaData
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

import settings

print(settings.SQLALCHEMY_DATABASE_URL)
engine = create_async_engine(
    settings.SQLALCHEMY_DATABASE_URL,
    echo=True,
    future=True,
)

# Use sessionmaker for async session creation
SessionLocal = sessionmaker(
    engine, 
    expire_on_commit=False, 
    class_=AsyncSession
)

metadata = MetaData()
Base = declarative_base(metadata=metadata)
