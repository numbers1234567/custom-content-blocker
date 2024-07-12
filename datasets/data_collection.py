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

target_dir = "datasets"
media_dirname = "media"
media_dir = os.path.join(target_dir, media_dirname)
if not os.path.isdir(target_dir): os.mkdir(target_dir)
if not os.path.isdir(media_dir): os.mkdir(media_dir)
main_filename = "main.csv"
media_filename = "media.csv"
current_split = "train"
current_label = 0

main_file  = os.path.join(target_dir, main_filename)
media_file = os.path.join(target_dir, media_filename)

target_file_lock = threading.Lock()

print(os.listdir(target_dir))
if main_filename not in os.listdir(target_dir):
    with open(main_file, "w+", encoding="utf-8") as f:
        f.write("ID\ttext\tlabel\tsplit\n")

if media_filename not in os.listdir(target_dir):
    with open(media_file, "w+", encoding="utf-8") as f:
        f.write("ID\tpath\n")
cur_id = 0
if pd.read_csv(main_file, delimiter="\t").empty:
    cur_id = 0
else:
    cur_id = pd.read_csv(main_file, delimiter="\t")["ID"].max() + 1
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
     open(os.path.join(target_dir, "main.csv"), "a", encoding="utf-8") as main, \
     open(os.path.join(target_dir, "media.csv"), "a", encoding="utf-8") as media:
        # Create file then add it to the media file
        for i,m in enumerate(post_info.media.images + post_info.media.video):
            filename = os.path.join(media_dir, "%d_%d.%s" % (cur_id, i, m.dataFormat))
            with open(filename, "wb+") as f:
                f.write(decode_b64media(m.content))
        for i,m in enumerate(post_info.media.images + post_info.media.video):
            filename = os.path.join(media_dirname, "%d_%d.%s" % (cur_id, i, m.dataFormat))
            media.write("%d\t%s\n" % (cur_id, filename))
        # Add to main file
        #main.write(f'{cur_id},"{post_info.media.text.replace('\n', '')}",{current_label},{current_split}\n')
        main.write('%d\t%s\t%d\t%s\n' % (cur_id, 
                                         post_info.media.text.replace('\n', '').replace("\t","").strip(), 
                                         current_label, 
                                         current_split))
        cur_id += 1


@app.post("/process_post/{user_key}/")
def process_post(user_key : str, post_info : PostInfo):
    save_post_data(post_info)
    return {"message" : "bruh"}

@app.post("/blocked_post/{user_key}")
def block_post(user_key : str, id : str):
    return 