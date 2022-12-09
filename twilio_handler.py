import os
from twilio.rest import Client

# Set environment variables for your credentials
# Read more at http://twil.io/secure
account_sid = "AC6a69c9fd7f4fbcc255268f99e7e9475a"
auth_token = os.environ["TWILIO_AUTH_TOKEN"]
client = Client(account_sid, auth_token)

message = client.messages.create(
  body="Hello from Twilio 2",
  from_="+12183077373",
  to="+12174198955"
)

print(message.sid)