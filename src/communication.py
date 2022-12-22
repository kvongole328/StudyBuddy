from flask import Flask, request, redirect,abort, make_response, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import gpt_handler
from flask_basicauth import BasicAuth
from twilio.request_validator import RequestValidator
from functools import wraps
from twilio.rest import Client 
import os, psycopg2, pypika
from flask_cors import CORS,cross_origin
import random

account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)
my_twilio_number = os.environ



def get_my_number():
    incoming_phone_numbers = client.incoming_phone_numbers.list()

    length_of_list = len(incoming_phone_numbers)
    if (length_of_list == 1): 
        return incoming_phone_numbers[0].phone_number
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

    conn = psycopg2.connect(database = os.environ['DATABASE_NAME'], user = os.environ['DATABASE_USER'], password = str(os.environ["DATABASE_PASSWORD"]),host = "oregon-postgres.render.com" ,port = '5432', sslmode='require')
    curr = conn.cursor() 
    # Getincoming message info 
    message_sid = message.sid
    from_number = number_to_use
    to_number = customer_number
    incoming_body = message.body
    print("ID:",message_sid)
    # Build Query
    messages = pypika.Table('messages')
    incoming_query = str(pypika.Query.into(messages).insert(message_sid, from_number, to_number,incoming_body)) 
    


    ##insert into DB 
    curr = conn.cursor()
    curr.execute(incoming_query);
    conn.commit()
    conn.close()
    
    #Get GPT Response

