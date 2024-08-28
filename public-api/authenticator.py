from data_models import Credentials
from data_store import DataStore
from dataclasses import dataclass

# Authentication
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

@dataclass
class UserData:
    email : str

class Authenticator:
    def __init__(self):
        pass

    def authenticate(credentials : Credentials) -> UserData:
        token = credentials.token
        try:
            idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)

            userid = idinfo['sub']
        except ValueError as e:
            raise Exception("Invalid token " + token)
        
        return UserData(email=idinfo["email"])