import stytch 
import os
import utils 
from datetime import datetime 
from utils import * 


client = stytch.Client(
project_id=os.environ['STYTCH_PROJECT_ID'],
secret=os.environ['STYTCH_PROJECT_SECRET'],
environment=os.environ['STYTCH_PROJECT_ENV'],
)

def create_user(phone_number): 
    #Stytch call to create the user 
    user_number = str(phone_number)
    resp = client.otps.sms.login_or_create(
        phone_number=user_number,
        create_user_as_pending = True
    )
    print("Resp error code type: ",type(resp.status_code))
    # Handle if status code is not 200 
    if resp.status_code != 200: 
        return resp
    #Build our user model
    print(type(resp))
    user_id = resp.user_id
    phone_id = resp.phone_id
    current_time = datetime.now() 
    is_paying = 0 
    is_verified = 0 

    #Add user to the data base 
    db_response = db_handler.add_user(user_id,user_number,phone_id,50,current_time,is_paying,is_verified) 

    ### return the user_id and phone_id to the front end
    return resp

def authenticate_user(code,user_id,method_id):
    ### get user_id, phone_id and string 
    user_id_string = str(user_id)
    method_id_string = str(method_id)
    code_string = str(code) 

    # Call Stytch 
    resp = client.otps.authenticate( 
        method_id = method_id_string,
        code = code_string
    )
    print("authenticate resp: ", resp)

    if resp.status_code == 200: 
     db_handler.verify_user(user_id_string)
    return(resp)



if __name__ == "__main__":
    user_id,phone_id = create_user("")
    otp = input("Enter otp: " )
    authenticate_user(user_id,phone_id,otp)
