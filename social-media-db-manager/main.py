
###############
#   IMPORTS   #
###############

# API
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Social Media Handlers
from SocialAPIHandlers.SocialClient import SocialClient
from SocialAPIHandlers.RedditClient import RedditClient

# Database
import psycopg2

# utility
import os
from pydantic import BaseModel


#################
#   CONSTANTS   #
#################

# Database
POSTGRES_DB_NAME = os.environ["CONTENT_CURATION_POSTGRES_DB_NAME"]
POSTGRES_DB_USER = os.environ["CONTENT_CURATION_POSTGRES_USER"]
POSTGRES_DB_PASS = os.environ["CONTENT_CURATION_POSTGRES_PASSWORD"]
POSTGRES_DB_HOST = os.environ["CONTENT_CURATION_POSTGRES_HOST"]
POSTGRES_DB_PORT = os.environ["CONTENT_CURATION_POSTGRES_PORT"]
POSTGRES_DB_URL = f'postgres://{POSTGRES_DB_USER}:{POSTGRES_DB_PASS}@{POSTGRES_DB_HOST}:{POSTGRES_DB_PORT}/{POSTGRES_DB_NAME}'


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

@app.post("/update_post_db/")
async def update_post_db(): 
    # Periodically run to add posts to database. Might be better to move this to a different service.
    pass

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