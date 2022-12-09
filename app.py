from flask import Flask, request, redirect
from twilio.twiml.messaging_response import MessagingResponse
import gpt_handler
app = Flask(__name__)

@app.route("/sms", methods=['GET', 'POST'])
def incoming_sms():
    """Send a dynamic reply to an incoming text message"""
    # Get the message the user sent our Twilio number
    body = request.values.get('Body', None)
    to_reply = gpt_handler.generate_response(body) 
    # Start our TwiML response
    resp = MessagingResponse()
    resp.message(to_reply)
    # Determine the right reply for this message


    return str(resp)

if __name__ == "__main__":
    app.run(debug=True)
