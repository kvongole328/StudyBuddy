from sqlalchemy.orm import declarative_base, sessionmaker
from sqlalchemy import Column,Integer, String, DateTime, create_engine
import os 

def Session(): 
    return sessionmaker(bind=create_engine(str(os.environ['database_connection'])))
