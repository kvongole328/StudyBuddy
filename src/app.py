from flask import Flask, request, redirect,abort
from twilio.twiml.messaging_response import MessagingResponse
import gpt_handler
from flask_basicauth import BasicAuth
from twilio.request_validator import RequestValidator
from functools import wraps
from twilio.rest import Client 
import os, psycopg2, pypika
from flask_cors import CORS,cross_origin

app = Flask(__name__)
CORS(app)
app.config['CORS_HEADERS'] = 'Content-Type'

app.config['BASIC_AUTH_USERNAME'] = os.environ['BASIC_AUTH_USERNAME']
app.config['BASIC_AUTH_PASSWORD'] = os.environ['BASIC_AUTH_PASSWORD']


conn = psycopg2.connect(database = os.environ['DATABASE_NAME'], user = os.environ['DATABASE_USER'], password = str(os.environ["DATABASE_PASSWORD"]),host = "oregon-postgres.render.com" ,port = '5432', sslmode='require')

curr = conn.cursor() 

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
    conn = psycopg2.connect(database = os.environ['DATABASE_NAME'], user = os.environ['DATABASE_USER'], password = str(os.environ["DATABASE_PASSWORD"]),host = "oregon-postgres.render.com" ,port = '5432', sslmode='require')

    curr = conn.cursor() 

    # Getincoming message info 
    incoming_message_sid = request.values.get('MessageSid')
    from_number = request.values.get('From')
    to_number = request.values.get('To')
    incoming_body = request.values.get('Body', None)

    # Build Query
    messages = pypika.Table('messages')
    incoming_query = str(pypika.Query.into(messages).insert(incoming_message_sid, from_number, to_number,incoming_body)) 
    


    ##insert into DB 
    curr = conn.cursor()
    curr.execute(incoming_query);
    conn.commit()
    
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

    outgoing_query = str(pypika.Query.into(messages).insert(outgoing_message_sid, from_number_outgoing, to_number_outgoing,outgoing_body))
    curr.execute(outgoing_query);
    conn.commit()

    return str(resp)


'''Send verification to phone number''' 
@app.route("/send-code", methods=['POST'])
@cross_origin()
@basic_auth.required
def send_code():
    phone_number = str(request.values.get('phone_number'))
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_service_id = os.environ['TWILIO_SERVICE_ID']

    client = Client(account_sid, auth_token)
    verification = client.verify \
                     .v2 \
                     .services(twilio_service_id) \
                     .verifications \
                     .create(to = "+"+"1"+phone_number, channel='sms')
    return (verification.status)

@app.route("/verify-code", methods=['POST'])
@cross_origin()
@basic_auth.required
def verify_code():
    received_code = request.values.get('verification_code')
    phone_number = str(request.values.get('phone_number'))
    account_sid = os.environ['TWILIO_ACCOUNT_SID']
    auth_token = os.environ['TWILIO_AUTH_TOKEN']
    twilio_service_id = os.environ['TWILIO_SERVICE_ID']
    client = Client(account_sid, auth_token)
    verification_check = client.verify \
                     .v2 \
                     .services(twilio_service_id) \
                     .verification_checks \
                     .create(to="+"+"1"+ phone_number, code=received_code)
    return (verification_check.status)



''' Test end point set up to verify that basic auth is working ''' 
@app.route("/test", methods=['GET', 'POST'])
@validate_twilio_request
@basic_auth.required 
def test():
    if request.method == 'POST':
        print("received POST Webhook")
        return "POST Webhook Received"
    if request.method == 'GET': 
        print("received GET WEbhook" )
        return "GET Webhook Received"



if __name__ == "__main__":
    app.run(debug=True)


