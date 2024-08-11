"""
Definition for a service which can be
    used to interface with Postgres
    database. Might be better as a 
    private service.
"""


###############
#   IMPORTS   #
###############

# API
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Social Media Handlers
from SocialAPIHandlers.SocialClient import SocialClient, SocialPostBaseData
from SocialAPIHandlers.RedditClient import RedditClient

# third-party services
from huggingface_hub import get_inference_endpoint

# Database
import psycopg2

# utility
import os
from pydantic import BaseModel

import json
import requests

import multiprocessing as mp

from typing import Union

import time


#################
#   CONSTANTS   #
#################

# Database
_POSTGRES_DB_NAME = os.environ["CONTENT_CURATION_POSTGRES_DB_NAME"]
_POSTGRES_DB_USER = os.environ["CONTENT_CURATION_POSTGRES_USER"]
_POSTGRES_DB_PASS = os.environ["CONTENT_CURATION_POSTGRES_PASSWORD"]
_POSTGRES_DB_HOST = os.environ["CONTENT_CURATION_POSTGRES_HOST"]
_POSTGRES_DB_PORT = os.environ["CONTENT_CURATION_POSTGRES_PORT"]

POSTGRES_DB_URL = f'postgres://{_POSTGRES_DB_USER}:{_POSTGRES_DB_PASS}@{_POSTGRES_DB_HOST}:{_POSTGRES_DB_PORT}/{_POSTGRES_DB_NAME}'

# Social Media APIs
_REDDIT_API_CLIENT_ID     = os.environ["CONTENT_CURATION_REDDIT_API_CLIENT_ID"]
_REDDIT_API_CLIENT_SECRET = os.environ["CONTENT_CURATION_REDDIT_API_CLIENT_SECRET"]
_REDDIT_API_PASSWORD      = os.environ["CONTENT_CURATION_REDDIT_API_PASSWORD"]
_REDDIT_API_USER_AGENT    = os.environ["CONTENT_CURATION_REDDIT_API_USER_AGENT"]
_REDDIT_API_USERNAME      = os.environ["CONTENT_CURATION_REDDIT_API_USERNAME"]

# HuggingFace inference endpoints
_HUGGINGFACE_ENDPOINT_URL  = os.environ["CONTENT_CURATION_HUGGINGFACE_ENDPOINT_URL"]
_HUGGINGFACE_ENDPOINT_NAME = os.environ["CONTENT_CURATION_HUGGINGFACE_ENDPOINT_NAME"]
_HUGGINGFACE_ACCESS_TOKEN  = os.environ["CONTENT_CURATION_HUGGINGFACE_ACCESS_TOKEN"]


############################
#   THIRD PARTY SERVICES   #
############################

huggingface_blip_endpoint = get_inference_endpoint(name=_HUGGINGFACE_ENDPOINT_NAME, token=_HUGGINGFACE_ACCESS_TOKEN)

def get_blip_features(text:str, has_image:bool, base_64_image:Union[None, str]=None):
    body = {
        "inputs" : {
            "text" : text, 
            "has_image" : base_64_image!=None, 
            "image" : base_64_image 
        }
    }

    feature_vector = json.loads(huggingface_blip_endpoint.client.post(json=body))["feature_vector"][0]

    return feature_vector


SOCIAL_CLIENTS = [
    RedditClient(_REDDIT_API_CLIENT_ID, _REDDIT_API_CLIENT_SECRET, _REDDIT_API_PASSWORD, _REDDIT_API_USERNAME, _REDDIT_API_USER_AGENT),
]


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

def check_post_exists_db(conn, post : SocialPostBaseData) -> bool:
    cur: psycopg2.cursor = conn.cursor()
    cur.execute("""
        SELECT * 
        FROM social_post_data
        WHERE post_id=%s;
    """, (post.metadata.post_id, ))
    db_post = cur.fetchone()
    cur.close()
    return db_post != None

def get_max_internal_id() -> int:
    conn = psycopg2.connect(POSTGRES_DB_URL)
    cur: psycopg2.cursor = conn.cursor()

    cur.execute("""
        SELECT MAX(internal_id)
        FROM social_post_data;
    """)

    result = cur.fetchone()

    max_id = result[0] if result[0]!=None else -1
    
    cur.close()
    conn.close()

    return max_id

def insert_post_db(post : SocialPostBaseData, add_id : int|None = None) -> bool:
    # Try to connect
    try:
        conn = psycopg2.connect(POSTGRES_DB_URL)
        cur = conn.cursor()
    except Exception as e:
        print(f"[ERROR]: Failed to connect to database!")
        print("   Error message " + str(e))
        return False

    # Make sure post has not been added
    if check_post_exists_db(conn, post):
        print(f"[Message]: Post {post.metadata.post_id} already exists in db!")
        return False
    
    try:
        if add_id == None: 
            add_id = get_max_internal_id(conn)+1

        
        cur.execute("""
            INSERT INTO social_post_data (internal_id, post_id, title, embed_html, create_utc) 
                VALUES (%s, %s, %s, %s, %s);
        """, (add_id, post.metadata.post_id, post.media_data.text, post.media_data.embed_html, post.metadata.create_utc))

        # Insert extra features here

        # BLIP features
        try:
            has_image = len(post.media_data.images_b64) > 0
            features = get_blip_features(post.media_data.text, has_image, post.media_data.images_b64[0].decode('utf-8') if has_image else None)

            cur.execute("""
                INSERT INTO blip_features (internal_id, features)
                    VALUES (%s, %s);
            """, (add_id, features))
        except Exception as e:
            print(f"[ERROR]: Failed to insert BLIP features for {post.metadata.post_id}!")
            print("   Error message " + str(e))

        conn.commit()

        cur.close()
        conn.close()

        print(f"[Message]: Inserted post {post.metadata.post_id}.")
        return True

    except Exception as e:
        print(f"[ERROR]: Failed to insert post {post.metadata.post_id} into database!")
        print("   Error message " + str(e))

        cur.close()
        return False

"""
Add posts to the database from social
    media APIs.

Expected to run every hour.
"""
@app.post("/update_post_db")
async def update_post_db(count : int=2000): 

    # Add posts to the database
    # Get maximum internal id (One concern is, if two calls to update_post_db() are made,
    #  they might both get the same maximum internal id, and there will be a conflict
    #  when inserting new posts. This is not an issue, since this should run periodically.
    #  However, if it comes to that, we could add a lock for this)
    def get_and_add_posts():
        huggingface_blip_endpoint.resume()
        # Wait for things to initialize
        huggingface_blip_endpoint.wait()


        max_id = get_max_internal_id()

        # Get all trending posts
        social_posts: list[SocialPostBaseData] = []
        for client in SOCIAL_CLIENTS:
            social_posts = []
            try:
                social_posts = client.get_relevant_posts()
            except Exception as e:
                print("[ERROR]: Failed to retrieve posts for " + str(client) + "!")
                print("   Error message: " + str(e))

            for post in social_posts:
                # Insert post in database
                try:
                    if insert_post_db(post, add_id=max_id+1): max_id += 1
                except Exception as e:
                    print(f"[ERROR]: Failed to insert post {post.metadata.post_id} into database!")
                    print("   Error message: " + str(e))
        
        huggingface_blip_endpoint.pause()

    # Process to return an indicator of successfully retrieved and started process.
    p = mp.Process(target=get_and_add_posts)
    p.start()
    
    return {}

@app.get("/recent_posts")
# just need to confirm I can retrieve posts from the database, then I can add some fancy curation features.
async def get_recent_posts(before : int, count : int=20):
    if count > 100: count = 100
    with psycopg2.connect(POSTGRES_DB_URL) as conn:
        cur = conn.cursor()
        # New to SQL, so there might be a more performant way to do this.
        # There's also possibility for indexing
        cur.execute("""
            SELECT embed_html, create_utc, post_id
            FROM social_post_data
            WHERE create_utc < %s
            ORDER BY create_utc DESC
            LIMIT %s;
        """, (before, count))
        embeds = cur.fetchall()
    return {"html_embeds" : [{"html" : embed, "create_utc" : create_utc, "post_id" : post_id}  for (embed,create_utc,post_id) in embeds]}