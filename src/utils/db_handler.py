from sqlalchemy import exc
import models 
from utils import session 

session_maker = session.Session()

def add_message(message_sid,from_number,to_number,body,time_stamp): 
    message = models.MessagesModel(message_sid=message_sid, from_number=from_number, to_number=to_number,body=body,time_stamp=time_stamp)

    with session_maker() as session:
        try:  
            session.add(message)
            session.commit()
        except exc.SQLAlchemyError as e: 
            print(type(e))
            return("Failed to add with error: ",type(e)) 

def add_user(id, phone_number,phone_id,message_limit,created,is_paying,verified):
    user = models.UserModel(id=id, phone_number = phone_number, phone_id = phone_id, message_limit = message_limit, created = created, is_paying = is_paying, verified = verified)
    with session_maker() as session:
        try:  
            session.add(user)
            session.commit()
        except exc.SQLAlchemyError as e: 
            print(type(e))
            return("Failed to add with error: ",type(e)) 

def verify_user(id): 
    with session_maker() as session: 
        user = session.query(models.UserModel).filter(models.UserModel.id ==id).update({'verified': 1})
       
        session.commit()
