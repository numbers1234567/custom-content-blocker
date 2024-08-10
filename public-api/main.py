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


########################
#   HTTP DATA MODELS   #
########################

class CurationMode(BaseModel):
    key : str
    name : str

class Credentials(BaseModel):
    token : str

class CurationSetting(BaseModel):
    curation_mode : CurationMode
    social_media_whitelist : list[CurationMode]
    trending_filters : list[CurationMode]

class CuratePostsRequestOptions(BaseModel):
    before : int  # UTC
    count_max : int = 10
    count_min : int = 5
    min_score : float = 0.5

# get_curated_posts
class CuratePostsRequestBody(BaseModel):
    credentials : Credentials
    curation_settings : CurationSetting
    options : CuratePostsRequestOptions

class CuratedPost(BaseModel):
    post_id : str
    create_utc : int
    html : str
    curate_score : float

class CuratedPostsResponseBody(BaseModel):
    posts : list[CuratedPost]


########################
#   PRIVATE SERVICES   #
########################

POST_DB_MANAGER = os.environ["CONTENT_CURATION_POST_DB_MANAGER"]
CURATOR = os.environ["CONTENT_CURATION_CURATOR"]

@cache
def get_recent_posts(before : int, count : int=20):
    # Query post db
    response = requests.get(f"{POST_DB_MANAGER}/recent_posts?before={before}&count={count}")
    html_embeds = json.loads(response.content)["html_embeds"]
    
    return html_embeds

def url_encode(arg : str):
    return arg.replace(":", "%3A").replace("/", "%2F")

@cache
def get_curate_score(post_id : str, curation_key : str) -> float:
    if curation_key=="half":
        return random.random()
    if curation_key=="all":
        return 1
    if curation_key=="no_politics":
        try:
            response = requests.get(f"{CURATOR}/get_curate_score?post_id={url_encode(post_id)}&curate_key=no_politics")
        except Exception as e:
            print(f"[ERROR]: Failed to retrieve curate score for post_id {post_id} and curate_key {curation_key}")
            print("   Error Message: " + str(e))
            return 1
        try:
            result = float(response.content)
        except Exception as e:
            print(f"[ERROR]: Could not convert response score to float.")
            print("   Error Message: " + str(e))

        # Clamp result
        return max(min(result, 1), 0)

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
    curated_posts : list[CuratedPost] = []

    social_posts = get_recent_posts(posts_before, count_max)

    # Score each post
    for post in social_posts:
        html_embed = post["html"]
        create_utc = post["create_utc"]
        post_id = post["post_id"]

        curation_scores = get_curate_score(post_id, curation_mode)

        curated_posts.append(
            CuratedPost(post_id=post_id, create_utc=create_utc, html=html_embed, curate_score=curation_scores)
        )

    # Sort descending by score
    curated_posts = sorted(curated_posts, key=lambda x : -x.curate_score)
    for idx,post in enumerate(curated_posts):
        if post.curate_score < min_score and idx >= count_min: 
            curated_posts = curated_posts[:idx]
            break

    return CuratedPostsResponseBody(posts=curated_posts)

class LoginRequestBody(BaseModel):
    username : str
    password : str

class LoginResponseBody(BaseModel):
    user_token : Union[str, None]


"""
A login endpoint which returns a token used
    for future requests.
"""
@app.post("/login")
def login(request : LoginRequestBody) -> LoginResponseBody:
    pass
    