from jose import jwt
from datetime import datetime,timedelta
from config import*
from fastapi import HTTPException

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