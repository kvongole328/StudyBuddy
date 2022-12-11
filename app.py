from flask import Flask, request, redirect,abort
from twilio.twiml.messaging_response import MessagingResponse
import gpt_handler
from flask_basicauth import BasicAuth
from twilio.request_validator import RequestValidator
from functools import wraps
import os

app = Flask(__name__)

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
    """Send a dynamic reply to an incoming text message"""
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    to_reply = gpt_handler.generate_response(body) 
    # Start our TwiML response
    resp = MessagingResponse()
    resp.message(to_reply)
    return str(resp)

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


