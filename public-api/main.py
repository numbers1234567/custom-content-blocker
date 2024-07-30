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
from typing import Dict

import json
import requests

from functools import cache

import random


########################
#   PRIVATE SERVICES   #
########################

POST_DB_MANAGER = os.environ["CONTENT_CURATION_POST_DB_MANAGER"]

@cache
def get_recent_posts(before : int, count : int=20):
    # Query post db
    response = requests.get(f"{POST_DB_MANAGER}/recent_posts?before={before}&count={count}")
    html_embeds = json.loads(response.content)["html_embeds"]
    
    return html_embeds

@cache
def get_curate_score(post_id : str, curation_key : str) -> float:
    if curation_key=="half":
        return random.random()
    if curation_key=="all":
        return 1
    if curation_key=="none":
        return 0


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

class CuratePostsRequestBody(BaseModel):
    username : str
    password : str
    before : int
    count_max : int = 20
    count_min : int = 5
    min_score : float = 0.5
    curation_key : str = "full"

class CuratedPost(BaseModel):
    post_id : str
    create_utc : int
    html : str
    curate_score : float

class CuratedPostsResponseBody(BaseModel):
    posts : list[CuratedPost]

@app.post("/get_curated_posts")
async def get_curated_posts(request : CuratePostsRequestBody) -> CuratedPostsResponseBody:
    username, password, \
    posts_before, count_max, count_min, \
    min_score, curation_key = \
        request.username, request.password,\
        request.before, request.count_max, request.count_min, \
        request.min_score, request.curation_key
    curated_posts : list[CuratedPost] = []
    print("Received! " + str(posts_before))

    social_posts = get_recent_posts(posts_before, count_max)

    # Score each post
    for post in social_posts:
        html_embed = post["html"]
        create_utc = post["create_utc"]
        post_id = post["post_id"]

        curation_scores = get_curate_score(post_id, curation_key)

        curated_posts.append(
            CuratedPost(post_id=post_id, create_utc=create_utc, html=html_embed, curate_score=curation_scores)
        )

    # Sort descending by score
    curated_posts = sorted(curated_posts, key=lambda x : -x.curate_score)
    for idx,post in enumerate(curated_posts):
        if post.curate_score < min_score and idx >= count_min: 
            curated_posts = curated_posts[:idx]
            break

    print(curated_posts)
    return CuratedPostsResponseBody(posts=curated_posts)