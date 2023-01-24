from flask import Flask, request, redirect,abort, make_response, jsonify
from twilio.twiml.messaging_response import MessagingResponse
import gpt_handler
from flask_basicauth import BasicAuth
from twilio.request_validator import RequestValidator
from functools import wraps
from twilio.rest import Client 
import os, psycopg2, pypika
from flask_cors import CORS,cross_origin
import communication
from utils import * 
from sqlalchemy import exc
import models 
import auth 
from datetime import datetime

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'
app.config['BASIC_AUTH_USERNAME'] = os.environ['BASIC_AUTH_USERNAME']
app.config['BASIC_AUTH_PASSWORD'] = os.environ['BASIC_AUTH_PASSWORD']



basic_auth = BasicAuth(app)


def validate_twilio_request(f):
    """Validates that incoming requests genuinely originated from Twilio"""
    @wraps(f)
    def decorated_function(*args, **kwargs):

        # Create an instance of the RequestValidator class
        validator = RequestValidator(os.environ['TWILIO_AUTH_TOKEN'])
        # Validate the request using its URL, POST data,
        # and X-TWILIO-SIGNATURE header
        print(request.url)
        request_valid = validator.validate(
            request.url,
            request.form,
            request.headers.get('X-TWILIO-SIGNATURE', ''))

        # Continue processing the request if it's valid, return a 403 error if
        # it's not
        if request_valid:
            return f(*args, **kwargs)
        else:
            print("here")
            return abort(403)
    return decorated_function



@validate_twilio_request
@app.route("/sms", methods=['GET', 'POST'])
@basic_auth.required 
def incoming_sms():

    # Getincoming message info 
    incoming_message_sid = str(request.values.get('MessageSid'))
    from_number = str(request.values.get('From'))
    to_number = str(request.values.get('To'))
    incoming_body = str(request.values.get('Body', None))
    time_stamp = datetime.now()
    
    #SQL Alchemy Commit to DB 
    db_message = db_handler.add_message(incoming_message_sid,from_number,to_number,incoming_body,time_stamp)
  
    #Get GPT Response
    to_reply = gpt_handler.generate_response(incoming_body) 
    # Start our TwiML response
    resp = MessagingResponse()
    resp.message(to_reply)

    #Update DB 
    outgoing_message_sid = incoming_message_sid 
    to_number_outgoing = request.values.get('From')
    from_number_outgoing = request.values.get('To')
    outgoing_body = to_reply 
    outgoing_time_stamp = datetime.now()
    
    db_message = db_handler.add_message(outgoing_message_sid+"og",from_number_outgoing,to_number_outgoing,outgoing_body,outgoing_time_stamp)

    return str(resp)

#### Stytch Create User path 
@app.route("/create_user",methods=['POST'])
@basic_auth.required 
def create_user():
    if request.method == "OPTIONS": 
        return _build_cors_preflight_response()
    print("request is:",request.values)
    phone_number = str(request.values.get('phone_number'))
    print("phone number is: ", phone_number)
    create_user_response = auth.create_user("+"+"1"+phone_number)

    ### Handle Error 
    if create_user_response.status_code!= 200:
        create_user_response = jsonify({"Status": create_user_response.status_code,"Error_Type": create_user_response.error_type, "Error_Message":create_user_response.error_message}) 
        create_user_response.headers.add("Access-Control-Allow-Origin","*")
        return create_user_response

    response = jsonify({"Status": create_user_response.status_code, "User_ID": create_user_response.user_id, "Phone_ID": create_user_response.phone_id})
    response.headers.add("Access-Control-Allow-Origin","*")

    return response 


#### New Stytch Verify Path 
@app.route("/validate_user",methods=['POST'])
@basic_auth.required 
def validate_user():
    if request.method == "OPTIONS": 
        return _build_cors_preflight_response()
    print("request is:",request.values)

    verification_code = str(request.values.get('verification_code'))
    phone_id= str(request.values.get('phone_id'))
    user_id = str(request.values.get('user_id'))
    phone_number = str(request.values.get('phone_number'))

    ##Call Stytch helper to validate 
    validation_response = auth.authenticate_user(verification_code,user_id,phone_id)
    ### Handle Error State 
    if validation_response.status_code!= 200:
        error_response = jsonify({"Status": validation_response.status_code,"Error_Type": validation_response.error_type, "Error_Message":validation_response.error_message}) 
        error_response.headers.add("Access-Control-Allow-Origin","*")
        return error_response
    
    ####Handle Success
    response = jsonify({"Status": validation_response.status_code, "User_ID": validation_response.user_id, "Phone_ID": validation_response.method_id})

    ###Send GPT Welcome 
    communication.welcome_message(phone_number)
    response.headers.add("Access-Control-Allow-Origin","*")
    return response 

'''Send verification to phone number''' 
@app.route("/send-code", methods=['POST'])
@basic_auth.required
def send_code():
    #CORS Preflight
    if request.method == "OPTIONS": 
        return _build_cors_preflight_response() 
    print("request is:",request.values)
    phone_number = str(request.values.get('phone_number'))
    print("phone number is: ", phone_number)
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_service_id = os.environ['TWILIO_SERVICE_ID']

    client = Client(account_sid, auth_token)
    verification = client.verify \
                     .v2 \
                     .services(twilio_service_id) \
                     .verifications \
                     .create(to = "+"+"1"+phone_number, channel='sms')
    response = jsonify({"status":verification.status})
    response.headers.add("Access-Control-Allow-Origin","*")
    return response


@app.route("/verify-code", methods=['POST'])
@basic_auth.required
def verify_code():
    #CORS Preflight
    if request.method == "OPTIONS": 
        return _build_cors_preflight_response() 
    received_code = request.values.get('verification_code')
    phone_number = str(request.values.get('phone_number'))
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_service_id = os.environ['TWILIO_SERVICE_ID']
    client = Client(account_sid, auth_token)
    print("phone number" , phone_number)
    verification_check = client.verify \
                     .v2 \
                     .services(twilio_service_id) \
                     .verification_checks \
                     .create(to="+"+"1"+ phone_number, code=received_code)
                    
    response = jsonify({"status":verification_check.status})
    response.headers.add("Access-Control-Allow-Origin","*")
    if (verification_check.status  == 'approved'):
        communication.welcome_message(phone_number)
    return verification_check.status



''' Test end point set up to verify that basic auth is working ''' 
@app.route("/test", methods=['GET', 'POST'])
#@validate_twilio_request
@basic_auth.required 
def test():
    if request.method == 'POST':
        print("received POST Webhook")
        return "POST Webhook Received"
    if request.method == 'GET': 
        print("received GET WEbhook" )
        return "GET Webhook Received"
    
   


def _build_cors_preflight_response(): 
    response = make_response() 
    response.headers.add("Access-Control-Allow-Origin", "*")
    response.headers.add("Access-Control-Allow-Headers", "*")
    response.headers.add("Access-Control-Allow-Methods", "*")
    return response
def _corsify_actual_response(response): 
    response.headers.add("Access-Control-Allow-Origin","*")
    return response


if __name__ == "__main__":
    app.run(debug=True)


