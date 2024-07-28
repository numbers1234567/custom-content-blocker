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
from SocialAPIHandlers.SocialClient import SocialClient, SocialPostData
from SocialAPIHandlers.RedditClient import RedditClient

# Database
import psycopg2

# utility
import os
from pydantic import BaseModel

import json
import requests

import multiprocessing as mp


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
_REDDIT_API_CLIENT_ID=os.environ["CONTENT_CURATION_REDDIT_API_CLIENT_ID"]
_REDDIT_API_CLIENT_SECRET=os.environ["CONTENT_CURATION_REDDIT_API_CLIENT_SECRET"]
_REDDIT_API_PASSWORD=os.environ["CONTENT_CURATION_REDDIT_API_PASSWORD"]
_REDDIT_API_USER_AGENT=os.environ["CONTENT_CURATION_REDDIT_API_USER_AGENT"]
_REDDIT_API_USERNAME=os.environ["CONTENT_CURATION_REDDIT_API_USERNAME"]

############################
#   SOCIAL MEDIA CLIENTS   #
############################

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

"""
Add posts to the database from social
    media APIs.

Expected to run every hour.
"""
@app.post("/update_post_db")
async def update_post_db(count : int=2000): 
    def check_post_exists_db(conn, post : SocialPostData) -> bool:
        cur: psycopg2.cursor = conn.cursor()
        cur.execute("""
            SELECT * 
            FROM social_post_data
            WHERE post_id=%s;
        """, (post.metadata.post_id, ))
        db_post = cur.fetchone()
        cur.close()
        return db_post != None
    
    def get_max_internal_id(conn) -> int:
        cur: psycopg2.cursor = conn.cursor()

        cur.execute("""
            SELECT MAX(internal_id)
            FROM social_post_data;
        """)

        result = cur.fetchone()

        max_id = result[0] if result[0]!=None else -1
        
        cur.close()

        return max_id
    
    def insert_post_db(conn, post : SocialPostData, max_id : int|None = None) -> bool:
        if check_post_exists_db(conn, post):
            print(f"[Message]: Post {post.metadata.post_id} already exists in db!")
            return False
        
        cur: psycopg2.cursor = conn.cursor()
        try:
            if max_id == None: 
                max_id = get_max_internal_id(conn)

            
            cur.execute("""
                INSERT INTO social_post_data (internal_id, post_id, embed_html, create_utc)
                    VALUES (%s, %s, %s, %s);
            """, (max_id+1, post.metadata.post_id, post.media_data.embed_html, post.metadata.create_utc))
            cur.close()

            print(f"[Message]: Inserted post {post.metadata.post_id}.")
            return True

        except Exception as e:
            print(f"[ERROR]: Failed to insert post {post.metadata.post_id} into database!")
            print("   Error message " + str(e))

            cur.close()
            return False

    # Add posts to the database
    # Get maximum internal id (One concern is, if two calls to update_post_db() are made,
    #  they might both get the same maximum internal id, and there will be a conflict
    #  when inserting new posts. This is not an issue, since this should run periodically.
    #  However, if it comes to that, we could add a lock for this)
    def get_and_add_posts():
        with psycopg2.connect(POSTGRES_DB_URL) as conn:
            max_id = get_max_internal_id(conn)

            # Get all trending posts
            social_posts: list[SocialPostData] = []
            for client in SOCIAL_CLIENTS:
                try:
                    social_posts += client.get_relevant_posts()
                except Exception as e:
                    print("[ERROR]: Failed to retrieve posts for " + str(client) + "!")
                    print("   Error message: " + str(e))

            # Insert post data into database
            for post in social_posts:
                try:
                    if insert_post_db(conn, post, max_id=max_id): max_id += 1
                except Exception as e:
                    print(f"[ERROR]: Failed to insert post {post.metadata.post_id} into database!")
                    print("   Error message " + str(e))

            conn.commit()

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
            SELECT embed_html, create_utc
            FROM social_post_data
            WHERE create_utc < %s
            ORDER BY create_utc DESC
            LIMIT %s;
        """, (before, count))
        embeds = cur.fetchall()
    return {"html_embeds" : [{"html" : embed, "create_utc" : create_utc}  for (embed,create_utc) in embeds]}