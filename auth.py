from jose import jwt
from datetime import datetime,timedelta
from config import*
from fastapi import HTTPException
from database import engine,AsyncSession,LocalSession
from models import *
from sqlalchemy import update

def create_token(user:str):
    payload={
        'sub':user,
        'exp':datetime.now()+timedelta(hours=1)
    }
    return jwt.encode(payload,SECRET,ALGORITHM)

def get_by_token(token:str):
    try:
        data=jwt.decode(token,SECRET,algorithms=[ALGORITHM])
        return data['sub']
    except:
        raise HTTPException(401, 'Вы не зарегистрированы')

async def check_prem(user):
    if not(user.until):return

    days=datetime.utcnow()-user.until
    if days>=timedelta(days=31):
        async with LocalSession() as db: #type:ignore
            await db.execute(update(User).filter(User.name==user.name).values(until=None, pro=0))
            await db.commit()
    