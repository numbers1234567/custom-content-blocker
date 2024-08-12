###############
#   IMPORTS   #
###############

# API
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

# utility
import os

from pydantic import BaseModel
from typing import Dict, Union

import json
import requests

from functools import cache

import random

from data_models import *
from env import *

# Authentication
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests

from sessions import SessionManager, Session, SessionUser


########################
#   SESSION HANDLING   #
########################

session_manager = SessionManager({"public" : Session()})


#################
#   ENDPOINTS   #
#################

app = FastAPI()
origins = [
    "http://localhost:3000",
    "https://content-curator.vercel.app",
    "https://content-curator-git-staging-angelo-pimientas-projects.vercel.app"
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/get_curated_posts")
async def get_curated_posts(request : CuratePostsRequestBody) -> CuratedPostsResponseBody:
    # Unpack request
    token, \
    posts_before, count_max, count_min, \
    min_score, curation_mode = \
        request.credentials.token,\
        request.options.before, request.options.count_max, request.options.count_min, \
        request.options.min_score, request.curation_settings.curation_mode.key
    
    curated_posts : CuratedPostBatch = session_manager[token].get_curated_posts(posts_before, curation_mode, count_max=count_max, count_min=count_min, min_score=min_score)

    return CuratedPostsResponseBody(posts=curated_posts.posts)


"""
A login endpoint which returns a token used
    for future requests.
"""
@app.post("/login")
def login(request : LoginRequestBody) -> LoginResponseBody:
    # Unpack request
    credentials = request.credentials
    token = credentials.token

    #  Authenticate token
    try:
        idinfo = id_token.verify_oauth2_token(token, google_requests.Request(), GOOGLE_CLIENT_ID)

        userid = idinfo['sub']
    except ValueError as e:
        print("[ERROR]: Failed to log in a user.")
        print("   Message: " + str(e))
        return LoginResponseBody(success=False)

    # Create new session w/ token and email
    session_manager.register_session(token, SessionUser(idinfo["email"]))
    print(session_manager)

    # Return success message
    return LoginResponseBody(success=True)

@app.post("/create_curation_mode")
def create_curation_mode(request : CreateCurationModeRequestBody) -> CreateCurationModeResponseBody:
    pass