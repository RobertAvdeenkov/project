from fastapi import FastAPI
from models import Base,Message
from database import engine,LocalSession,DATABASE_URL
from datetime import datetime
from tasks.tasks import router
import os
from sqlalchemy import create_engine


app=FastAPI()
try:
    if 'aiosqlite' in DATABASE_URL:
        url=DATABASE_URL.replace('+aiosqlite', '')
    elif '+asyncpg' in DATABASE_URL:
        url=DATABASE_URL.replace('+asyncpg','')
    engine_sync=create_engine(url)
    Base.metadata.create_all(bind=engine_sync)
except Exception as e:
    print(e)

app.include_router(router=router)