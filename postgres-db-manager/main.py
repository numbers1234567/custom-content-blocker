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
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware

# Social Media Handlers
from .SocialAPIHandlers.SocialClient import SocialClient, SocialPostBaseData
from .SocialAPIHandlers.RedditClient import RedditClient
from .SocialAPIHandlers.YoutubeClient import YoutubeClient

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
import threading

from typing import Union,Dict,Tuple,Generator
from collections.abc import Iterable

import time

from backend_shared.data_models_http import *
import random

import numpy as np


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
reddit_api_access = True
youtube_api_access = True
try:
    _REDDIT_API_CLIENT_ID     = os.environ["CONTENT_CURATION_REDDIT_API_CLIENT_ID"]
    _REDDIT_API_CLIENT_SECRET = os.environ["CONTENT_CURATION_REDDIT_API_CLIENT_SECRET"]
    _REDDIT_API_PASSWORD      = os.environ["CONTENT_CURATION_REDDIT_API_PASSWORD"]
    _REDDIT_API_USER_AGENT    = os.environ["CONTENT_CURATION_REDDIT_API_USER_AGENT"]
    _REDDIT_API_USERNAME      = os.environ["CONTENT_CURATION_REDDIT_API_USERNAME"]
except:
    print("[LOG]: No access to Reddit API. Continuing without.")
    reddit_api_access = False

try:
    YOUTUBE_API_KEY = os.environ["CONTENT_CURATION_YT_DATA_KEY"]
except:
    print("[LOG]: No access to YouTube API. Continuing without.")
    youtube_api_access = False

# HuggingFace inference endpoints
huggingface_access = True
try:
    _HUGGINGFACE_ENDPOINT_URL  = os.environ["CONTENT_CURATION_HUGGINGFACE_ENDPOINT_URL"]
    _HUGGINGFACE_ENDPOINT_NAME = os.environ["CONTENT_CURATION_HUGGINGFACE_ENDPOINT_NAME"]
    _HUGGINGFACE_ACCESS_TOKEN  = os.environ["CONTENT_CURATION_HUGGINGFACE_ACCESS_TOKEN"]
except:
    print("[LOG]: No access to HuggingFace endpoint. Continuing without.")
    huggingface_access = False


############################
#   THIRD PARTY SERVICES   #
############################

huggingface_blip_endpoint = None
if huggingface_access:
    huggingface_blip_endpoint = get_inference_endpoint(name=_HUGGINGFACE_ENDPOINT_NAME, token=_HUGGINGFACE_ACCESS_TOKEN)

def get_blip_features(text:str, has_image:bool, base_64_image:Union[None, str]=None):
    if not huggingface_blip_endpoint: return None
    body = {
        "inputs" : {
            "text" : text, 
            "has_image" : base_64_image!=None, 
            "image" : base_64_image 
        }
    }

    feature_vector = json.loads(huggingface_blip_endpoint.client.post(json=body))["feature_vector"][0]

    return feature_vector


SOCIAL_CLIENTS = []
if reddit_api_access:  SOCIAL_CLIENTS.append(RedditClient(_REDDIT_API_CLIENT_ID, _REDDIT_API_CLIENT_SECRET, _REDDIT_API_PASSWORD, _REDDIT_API_USERNAME, _REDDIT_API_USER_AGENT))
if youtube_api_access: SOCIAL_CLIENTS.append(YoutubeClient(YOUTUBE_API_KEY))


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

def get_user_data(email : str) -> Tuple[str,str,str,List[CurationMode]]:
    try:
        conn = psycopg2.connect(POSTGRES_DB_URL)
    except:
        raise Exception(status_code=500, detail="Failed to connect to database. Check credentials")
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT email, user_id, create_utc FROM user_credentials
            WHERE email=%s;
        """, (email, ))
        main_data = cur.fetchone()
    except:
        raise Exception("Failed to query database.")
    
    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT curation_key,curation_name FROM curation_modes 
            WHERE primary_user IN (
                SELECT user_id FROM user_credentials WHERE email=%s
            );
        """, (email, ))
        curation_keys = cur.fetchall()
        curation_modes = [CurationMode(key=key, name=name) for key,name in curation_keys]
    except Exception as e:
        raise Exception(f"Failed to retrieve curation modes for {email}")
    
    if main_data==None:
        raise Exception(f"User {email} does not exist.")

    email,user_id,create_utc = main_data
    return email,user_id,create_utc,curation_modes

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
            features = get_blip_features(post.media_data.text, has_image, post.media_data.images_b64[0] if has_image else None)

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
max_id = get_max_internal_id()
num_left = 0

max_id_lock = threading.Lock()
num_left_lock = threading.Lock()
@app.post("/update_post_db")
async def update_post_db(): 
    if not huggingface_blip_endpoint:
        raise HTTPException(status_code=400, detail="Server does not have access to HuggingFace endpoint.")
    # Add posts to the database
    # Get maximum internal id (One concern is, if two calls to update_post_db() are made,
    #  they might both get the same maximum internal id, and there will be a conflict
    #  when inserting new posts. This is not an issue, since this should run periodically.
    #  However, if it comes to that, we could add a lock for this)


    def get_and_add_posts(social_posts : Iterable[SocialPostBaseData]):
        # Scary
        global num_left
        global max_id
        with num_left_lock:
            if num_left_lock==0:
                huggingface_blip_endpoint.resume()
                # Wait for things to initialize
                huggingface_blip_endpoint.wait()
            num_left += 1

        # Try to insert every post
        for post in social_posts:
            try:
                with max_id_lock:
                    add_id = max_id + 1
                    max_id += 1
                insert_post_db(post, add_id=add_id)
            
            except Exception as e:
                # Unknown exception
                print(f"[ERROR]: Failed to insert post {post.metadata.post_id}.")
                print("   Message: " + str(e))
        
        with num_left_lock:
            num_left -= 1
            if num_left <= 0:
                huggingface_blip_endpoint.pause()

    social_post_generators : List[Generator[SocialPostBaseData, None, None]] = [client.get_relevant_posts() for client in SOCIAL_CLIENTS]
    # Thread for each social platform
    for social_post_generator in social_post_generators:
        thread = threading.Thread(target=get_and_add_posts, args=[social_post_generator])
        thread.start()
    
    return {}

@app.get("/recent_posts")
async def get_recent_posts(before : int, count : int=20) -> GetRecentPostsResponseBody:
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
    return GetRecentPostsResponseBody(
        html_embeds=[HTMLEmbed(html=html,create_utc=create_utc,post_id=post_id) for (html, create_utc, post_id) in embeds]
    )

def get_max_curate_id():
    conn = psycopg2.connect(POSTGRES_DB_URL)
    cur: psycopg2.cursor = conn.cursor()

    cur.execute("""
        SELECT MAX(curation_id)
        FROM curation_modes;
    """)

    result = cur.fetchone()

    max_id = result[0] if result[0]!=None else -1
    
    cur.close()
    conn.close()

    return max_id

def create_formatted_str_array(arr : Iterable[any]) -> str:
    return "{" + ",".join([str(i) for i in arr]) + "}"

max_curate_id_lock = mp.Lock()
whitelist_key_characters = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
@app.post("/create_curation_mode")
async def _endpoint_create_curation_mode(request : CreateCurationModeRequestBody) -> CreateCurationModeResponseBody:
    # Unpack request
    email,curation_name = request.credentials.email,request.mode_name
    curation_key : str|None = None
    curation_id : str|None = None

    email,user_id,_,_ = get_user_data(email)

    create_utc = time.time()
    max_curate_id_lock.acquire()
    # DB should reject non-unique keys, so keep trying
    curation_key = ""
    tries = 0
    MAX_TRIES = 4
    while tries < MAX_TRIES:  # Either a statistical anomaly (curation key exists) or an unknown exception
        try:
            with psycopg2.connect(POSTGRES_DB_URL) as conn:
                curation_key = "".join([random.choice(whitelist_key_characters) for _ in range(40)])
                curation_id = get_max_curate_id()+1
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO curation_modes (primary_user, curation_id, curation_name, curation_key, create_utc) 
                    VALUES (%s, %s, %s, %s, %s);
                """, (user_id, curation_id, curation_name, curation_key, create_utc))
                conn.commit()
                cur.close()
            break
                
        except Exception as e:
            print(f"[ERROR]: Attempt {tries+1} to insert {curation_name} for {user_id} failed!")
            print("   Message: " + str(e))
            pass
        tries += 1
    if tries >= MAX_TRIES:
        print(f"[ERROR]: Failed to insert curation mode with user {user_id} and name {curation_name}.")
        max_curate_id_lock.release()
        raise HTTPException(status_code=500, detail="")
    max_curate_id_lock.release()
    return CreateCurationModeResponseBody(
        curation_mode=CurationMode(
            key=curation_key,
            name=curation_name
        )
    )
    
def get_max_uid() -> int:
    try:
        conn = psycopg2.connect(POSTGRES_DB_URL)
    except:
        raise HTTPException(status_code=500, detail="Failed to connect to database. Check credentials.")
    
    cur = conn.cursor()
    
    cur.execute("""
        SELECT MAX(user_id)
        FROM user_credentials;
    """)

    result = cur.fetchone()

    max_id = result[0] if result[0]!=None else -1
    
    cur.close()
    conn.close()

    return max_id
    
max_uid_lock = mp.Lock()
@app.post("/sign_up_user")
async def _endpoint_sign_up_user(request : SignUpUserRequestBody) -> SignUpUserResponseBody:
    try:
        conn = psycopg2.connect(POSTGRES_DB_URL)
    except:
        raise HTTPException(status_code=500, detail="Failed to connect to database. Check credentials.")\
    # Unpack request
    email = request.credentials.email
    
    cur = conn.cursor()
    with max_uid_lock:
        next_uid = get_max_uid() + 1
        create_utc = time.time()
        try:  # Insert user
            cur.execute("""
                INSERT INTO user_credentials (user_id, create_utc, email)
                VALUES (%s, %s, %s);
            """, (next_uid, create_utc, email))
            conn.commit()

            conn.close()
            cur.close()

        except Exception as e:
            print(f"[ERROR]: Failed to create user {email}.")
            print("   Message: " + str(e))
            raise HTTPException(status_code=500, detail=f"Failed to create user {email}.")
    
    return SignUpUserResponseBody(success=True)

@app.post("/get_user_data")
async def _endpoint_get_user_data(request : GetUserDataRequestBody) -> GetUserDataResponseBody:
    email = request.email
    

    email,user_id,create_utc,curate_modes = get_user_data(email)
    return GetUserDataResponseBody(email=email, uid=user_id, create_utc=create_utc,curate_modes=curate_modes)

@app.post("/delete_curation_mode")
async def _endpoint_delete_curation_mode(request : DeleteCurationModeRequestBody) -> DeleteCurationModeResponseBody:
    try:
        conn = psycopg2.connect(POSTGRES_DB_URL)
    except:
        raise HTTPException(status_code=500, detail="Failed to connect to database. Check credentials.")
    
    curate_key = request.curation_key

    cur = conn.cursor()

    cur.execute("""
        DELETE FROM curation_modes
        WHERE curation_key=%s;
    """, (curate_key,))
    conn.commit()

    return DeleteCurationModeResponseBody()