from models import Base, Message
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import os
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession,create_async_engine

DATABASE_URL=os.getenv('DATABASE_URL', 'sqlite+aiosqlite:///messagesDB.db')
engine=create_async_engine(DATABASE_URL)
LocalSession=sessionmaker(bind=engine, class_=AsyncSession ,expire_on_commit=False) #type:ignore

async def get_db():
    async with LocalSession() as db: #type:ignore
        try:
            yield db
        finally:
            await db.close()