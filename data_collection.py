"""
How to collect data:
 * Start the server.
 * Start the blocker extension, changing the API url to this process
 * Navigate to any subreddit. The posts will automatically be sent here, and relevant data will be written to the target file.
"""
# System
import sys
sys.path.append("BLIP")
import os
import threading
import base64

# DS
import pandas as pd
from models.blip import blip_feature_extractor

target_dir = "datasets"
main_filename = "main.csv"
media_filename = "media.csv"
current_split = "train"
current_label = 1

main_file  = os.path.join(target_dir, main_filename)
media_file = os.path.join(target_dir, media_filename)

target_file_lock = threading.Lock()

print(os.listdir(target_dir))
if main_filename not in os.listdir(target_dir):
    with open(main_file, "w+") as f:
        f.write("ID,text,label,split")

if media_filename not in os.listdir(target_dir):
    with open(media_file, "w+") as f:
        f.write("ID,path")
cur_id = 0
if pd.read_csv(main_file).empty:
    cur_id = 0
else:
    cur_id = pd.read_csv(main_file)["ID"].max() + 1
#cur_id = pd.read_csv("")

# API
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from fastapi.middleware.cors import CORSMiddleware


origins = [
    "https://www.reddit.com"
]

class Media(BaseModel):
    content : str
    dataFormat : str

class MediaData(BaseModel):
    text : str
    images : list[Media] = []
    video : list[Media] = []

class Metadata(BaseModel):
    id : str

class PostInfo(BaseModel):
    media : MediaData
    metadata : Metadata


app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

def decode_b64media(media : str):
    return base64.b64decode(media)

def save_post_data(post_info : PostInfo):
    global cur_id
    with target_file_lock, \
     open(os.path.join(target_dir, "main.csv"), "a") as main, \
     open(os.path.join(target_dir, "media.csv"), "a") as media:
        # Create file then add it to the media file
        for i,m in enumerate(post_info.media.images + post_info.media.video):
            filename = os.path.join("media", "%d_%d.%s" % (cur_id, i, m.dataFormat))
            with open(os.path.join(target_dir, filename), "wb+") as f:
                f.write(decode_b64media(m.content))
        for i,m in enumerate(post_info.media.images + post_info.media.video):
            media.write("%d,%s\n" % (cur_id, filename))
        # Add to main file
        main.write(f'{cur_id},"{post_info.media.text}",{current_label},{current_split}\n')
        cur_id += 1


@app.post("/process_post/{user_key}/")
def process_post(user_key : str, post_info : PostInfo):
    save_post_data(post_info)
    return {"message" : "bruh"}

@app.post("/blocked_post/{user_key}")
def block_post(user_key : str, id : str):
    return 