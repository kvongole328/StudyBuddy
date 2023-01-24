from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column,Integer, String, DateTime, create_engine
from datetime import datetime
import os

Base = declarative_base()

class UserModel(Base): 
    __tablename__ = 'users'

     
    id = Column(String, primary_key = True) 
    phone_number = Column(String, nullable = False) 
    phone_id = Column(String) 
    message_limit = Column(Integer) 
    created = Column(DateTime,default=datetime.utcnow) 
    is_paying = Column(Integer, default = 0) 
    verified = Column(Integer , default = 0)

class MessagesModel(Base): 
    __tablename__ = 'text_messages' 
    message_sid = Column(String, primary_key = True) 
    from_number = Column(String) 
    to_number = Column(String) 
    body = Column(String(1600))
    time_stamp = Column(DateTime,default=datetime.utcnow)




