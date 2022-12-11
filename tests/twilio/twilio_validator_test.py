# Download the twilio-python library from twilio.com/docs/python/install
from twilio.request_validator import RequestValidator
from requests.auth import HTTPBasicAuth
import requests
import urllib
import os

# Your Auth Token from twilio.com/user/account saved as an environment variable
# Remember never to hard code your auth token in code, browser Javascript, or distribute it in mobile apps
auth_token = '3ab0315739eaef8d15400a62e10d5e94'
validator = RequestValidator(auth_token)
print("validator:",validator)

# Replace this URL with your unique URL
url = "http://a443-136-49-75-181.ngrok.io/test"
# User credentials if required by your web server. Change to 'HTTPBasicAuth' if needed
auth = HTTPBasicAuth('test', 'test')

params = {
    'CallSid': 'CA1234567890ABCDE',
    'Caller': '+12349013030',
    'Digits': '1234',
    'From': '+12349013030',
    'To': '+18005551212'
}

def test_url(method, url, params, valid):
    if method == "GET":
        url = url + '?' + urllib.parse.urlencode(params)
        params = {}

    if valid:
        signature = validator.compute_signature(url, params)
    else:
        signature = validator.compute_signature("http://invalid.com", params)

    headers = {'X-Twilio-Signature': signature}
    print(headers)
    response = requests.request(method, url, headers=headers, data=params, auth=auth)
    print(response)
    print('HTTP {0} with {1} signature returned {2}'.format(method, 'valid' if valid else 'invalid', response.status_code))


test_url('GET', url, params, True)
test_url('GET', url, params, False)
test_url('POST', url, params, True)
test_url('POST', url, params, False)