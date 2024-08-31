###############
#   IMPORTS   #
###############

# API
from fastapi import FastAPI, HTTPException
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

from backend_shared.data_models_http import *
from .env import *

from .sessions import SessionManager, Session, SessionUser

########################
#   SESSION HANDLING   #
########################

session_manager = SessionManager(default_sessions={"public" : Session()})


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
    
    if token==None or token not in session_manager:
        raise HTTPException(status_code=401, detail="No session exists for the user.")
    
    if count_max > 50 or count_max <= 0:
        raise HTTPException(status_code=400, detail="Invalid range. Constraint: 0 < count_max <= 50")
    if count_min > 50 or count_min <= 0:
        raise HTTPException(status_code=400, detail="Invalid range. Constraint: 0 < count_min <= 50")
    if count_min > count_max:
        raise HTTPException(status_code=400, detail="Invalid range. Constraint: count_min <= count_max")
    
    try:
        curated_posts : CuratedPostBatch = session_manager[token].get_curated_posts(posts_before, curation_mode, count_max=count_max, count_min=count_min, min_score=min_score)
    except Exception as e:
        print("[ERROR]: Failed to retrieve curated posts.")
        print("   Message: " + str(e))
        raise HTTPException(status_code=500, detail="Failed to retrieve curated posts")

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

    if not session_manager.login(credentials):
        print("[ERROR]: Failed to login with token " + token)
        raise HTTPException(status_code=401, detail="Invalid credentials.")


    # Return success message
    return LoginResponseBody(success=True)

@app.post("/create_curation_mode")
def create_curation_mode(request : CreateCurationModeRequestBody) -> CreateCurationModeResponseBody:
    # Unpack request
    token, mode_name = request.credentials.token, request.mode_name
    
    if token not in session_manager:
        raise HTTPException(status_code=401, detail="No session exists for the user.")
    
    session = session_manager[token]
    if not isinstance(session, SessionUser):
        raise Exception("[ERROR]: Session is not an authenticated session")
    
    try:
        curation_mode = session_manager[token].create_curation_mode(mode_name)
        
    except Exception as e:
        print("[ERROR]: Failed to create curation mode")
        print("   Message: " + str(e))
        raise HTTPException(status_code=500, detail="Failed to create curation mode.")
    
    if not curation_mode:
        raise HTTPException(status_code=400, detail="User is not allowed to create a new curation mode.")

    return CreateCurationModeResponseBody(curation_mode=curation_mode)

@app.post("/recommend_post")
def recommend_post(request : RecommendPostRequestBody) -> RecommendPostResponseBody:
    # Unpack request
    token,curate_key,post_id,positive = request.credentials.token,request.curate_key,request.post_id,request.options.positive
    
    if token not in session_manager:
        raise HTTPException(status_code=401, detail="No session exists for the user.")
    result = True
    try:
        session = session_manager[token]
        if not isinstance(session, SessionUser):
            raise Exception("[ERROR]: Session is not an authenticated session")
        
        result = session.recommend_post(curate_key,post_id,positive)
        
    except Exception as e:
        print("[ERROR]: Failed to recommend post")
        print("   Message: " + str(e))
        raise HTTPException(status_code=500, detail="Failed to recommend post.")

    if not result:
        raise HTTPException(status_code=401, detail="User is not allowed to modify this curation mode.")

    return RecommendPostResponseBody()