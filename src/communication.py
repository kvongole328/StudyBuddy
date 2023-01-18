from flask import Flask, request, redirect,abort, make_response, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import gpt_handler
from flask_basicauth import BasicAuth
from twilio.request_validator import RequestValidator
from functools import wraps
from twilio.rest import Client 
import os, psycopg2, pypika
from flask_cors import CORS,cross_origin
import utils 
import models 
import random
from sqlalchemy import exc


account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)
my_twilio_number = os.environ


### Retrieve numbers available on my Twilio account. Returns 1 by default 
def get_my_number():
    incoming_phone_numbers = client.incoming_phone_numbers.list()

    length_of_list = len(incoming_phone_numbers)
    #If I only have 1 number, get that 
    if (length_of_list == 1): 
        return incoming_phone_numbers[0].phone_number
    #Else pick a number from random 
    else:
        index = random.randint(0,length_of_list)
        return incoming_phone_numbers[index].phone_number

def welcome_message(customer_number): 
    number_to_use = get_my_number() 
    message = client.messages \
                .create(
                     body="Hi - I'm your always on GPT-3 bot! You can ask me almost anything - even the airspeed velocity of an unladen swallow!",
                     from_= number_to_use,
                     to=customer_number
                 )

    # Get message info 
    message_sid = message.sid
    from_number = number_to_use
    to_number = customer_number
    incoming_body = message.body
    print("ID:",message_sid)
    
    # Build Query and add to DB 
    message = models.MessagesModel(message_sid = str(message_sid), from_number = str(number_to_use), to_number = "+1"+str(customer_number), body = str(incoming_body))
    session_maker = utils.Session() 
    with session_maker() as session: 
        try: 
            session.add(message)
            session.commit() 
        except exc.SQLAlchemyError as e:
            print(type(e))
     
            
    messages = pypika.Table('messages')
    incoming_query = str(pypika.Query.into(messages).insert(message_sid, from_number, to_number,incoming_body)) 
    


