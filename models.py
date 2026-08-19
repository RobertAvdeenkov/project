from sqlalchemy import Column,String,Integer,DateTime,func,Boolean,ForeignKey
from sqlalchemy.orm import DeclarativeBase,relationship

class Base(DeclarativeBase):pass

class User(Base):
    __tablename__='users'
    id=Column(Integer,primary_key=True)
    name=Column(String)
    password=Column(String)
    pro=Column(Integer, default=0, nullable=False)

    ip=Column(String)
    until=Column(DateTime, default=None)

    messages=relationship('Message', back_populates='user')
    likes=relationship('Like', back_populates='user')

class Message(Base):
    __tablename__='textusers'
    id=Column(Integer,primary_key=True)
    school=Column(String)
    name=Column(String)
    category=Column(String)
    text=Column(String)
    created_at=Column(DateTime, default=func.now())
    user_id=Column(Integer,ForeignKey('users.id'))

    user=relationship('User', back_populates='messages')
    likes_count=Column(Integer,default=0)
    likes=relationship('Like',back_populates='message')

class Like(Base):
    __tablename__='likes'
    id=Column(Integer,primary_key=True)
    user_id=Column(Integer, ForeignKey('users.id'))
    message_id=Column(Integer,ForeignKey('textusers.id'))

    user=relationship('User',back_populates='likes')
    message=relationship('Message',back_populates='likes')

class Promo(Base):
    __tablename__='promo'
    id=Column(Integer,primary_key=True)
    value=Column(String)
    level=Column(Integer, default=1)

class Baned(Base):
    __tablename__='banned'
    id=Column(Integer,primary_key=True)
    ip=Column(String)