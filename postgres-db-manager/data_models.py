from pydantic import BaseModel
from typing import Dict, List


class HTMLEmbed(BaseModel):
    html : str
    create_utc : int
    post_id : str

class GetRecentPostsResponseBody(BaseModel):
    html_embeds : List[HTMLEmbed]

class CreateCurationModeRequestBody(BaseModel):
    email : str
    curation_name : str

class CreateCurationModeResponseBody(BaseModel):
    curation_key : str
    curation_name : str
    curation_id : int

class UserCredentials(BaseModel):
    email : str

class SignUpUserRequestBody(BaseModel):
    credentials : UserCredentials

class SignUpUserResponseBody(BaseModel):
    success : bool

class GetUserDataRequestBody(BaseModel):
    email : str

class GetUserDataResponseBody(BaseModel):
    email : str
    uid : int
    create_utc : int