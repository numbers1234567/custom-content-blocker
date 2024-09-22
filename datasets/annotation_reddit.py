import os
# Define target files here
MEDIA_DIR = "media" # Directory to dump media",
MAIN_CSV = "main.csv" # Directory for main definitions",
MEDIA_CSV = "media.csv" # Directory to track media"

from typing import Generator
import praw
import json
import requests
import time
import base64

reddit = praw.Reddit(
    client_id=os.environ["CONTENT_CURATION_REDDIT_API_CLIENT_ID"],
    client_secret=os.environ["CONTENT_CURATION_REDDIT_API_CLIENT_SECRET"],
    password=os.environ["CONTENT_CURATION_REDDIT_API_PASSWORD"],
    user_agent=os.environ["CONTENT_CURATION_REDDIT_API_USER_AGENT"],
    username=os.environ["CONTENT_CURATION_REDDIT_API_USERNAME"],
)

# Lifted from postgres-db-manager

def clean_image_url(url : str) -> str:
    return url.replace("&amp;", "&")

def get_imgs(post):
    base_url = post.url
    img_urls = []
    # It is a single image
    if "i.redd.it" in base_url:
        print(f"[LOG]: {base_url} is an image post")
        img_urls.append(base_url)

    print(f"[LOG]: Retrieving gallery images for {base_url}")
    # It is a gallery of images
    try:  # Possible things could go wrong with all of these accesses
        for media in post.gallery_data['items']:
            media_id = media["media_id"]

            metadata = post.media_metadata[media_id]

            # Only images
            if metadata["e"] != "image":
                continue

            best_version = (-1000, "")  # (size, url)
            for version in metadata['p'] + [metadata['s']]:
                size = version["x"]*version["y"]
                if size > 1000*1000: continue  # Too big 

                best_version = max(best_version, (size, version['u']))
            if best_version[0] > 0:
                img_urls.append(clean_image_url(best_version[1]))

    except Exception as e:
        print(f"[LOG]: Could not find gallery images for {base_url}")
        print("   Error: " + str(e))

    # Convert images
    imgs = []
    for url in img_urls:
        try:
            imgs.append(requests.get(url).content)
        except:
            print(f"[ERROR]: Failed to retrieve image {url} for {base_url}!")
            print("   Error: " + str(e))
    return imgs

def get_text(post):
    return post.title


import psycopg2
import random
import threading
from typing import List,Tuple,Any,Generator
MAX_UTC = 1e18
MAX_ID = 1e18

_POSTGRES_DB_NAME = os.environ["CONTENT_CURATION_POSTGRES_DB_NAME"]
_POSTGRES_DB_USER = os.environ["CONTENT_CURATION_POSTGRES_USER"]
_POSTGRES_DB_PASS = os.environ["CONTENT_CURATION_POSTGRES_PASSWORD"]
_POSTGRES_DB_HOST = os.environ["CONTENT_CURATION_POSTGRES_HOST"]
_POSTGRES_DB_PORT = os.environ["CONTENT_CURATION_POSTGRES_PORT"]
postgres_db_url = f'postgres://{_POSTGRES_DB_USER}:{_POSTGRES_DB_PASS}@{_POSTGRES_DB_HOST}:{_POSTGRES_DB_PORT}/{_POSTGRES_DB_NAME}'

def get_post_data_worker(post_id : str, target : List[Any]):
    post = reddit.submission(url=post_id)
    target.append(get_text(post))
    target.append(get_imgs(post))

def post_data_generator(postgres_db_url, utc_range=(0,MAX_UTC), id_range=(0,MAX_ID)) -> Generator[Tuple[str,str,List[bytes]], None, None]:
    min_utc,max_utc = utc_range
    min_id,max_id = id_range

    # Query DB
    conn = psycopg2.connect(postgres_db_url)

    cur = conn.cursor()
    cur.execute("""
        SELECT post_id FROM social_post_data
        WHERE internal_id <= %s AND internal_id >= %s AND create_utc <= %s AND create_utc >= %s;
    """, (max_id, min_id, max_utc, min_utc))

    # Get all reddit posts
    reddit_prefix = 'https://www.reddit.com'
    post_ids = [i for i, in cur.fetchall() if i[:len(reddit_prefix)]==reddit_prefix]
    random.shuffle(post_ids)

    # Main generator logic. Exits the function after the yield, so proactively get post data for responsiveness
    post = reddit.submission(url=post_ids[0])
    last_id,last_text,last_imgs = post_ids[0],get_text(post),get_imgs(post)
    for next_post_id in post_ids[1:]:
        next_result = []
        next_post_worker = threading.Thread(target=get_post_data_worker, args=(next_post_id,next_result))
        next_post_worker.start()
        
        yield last_id,last_text,last_imgs

        # Next loop setup
        next_post_worker.join()
        last_id,last_text,last_imgs = next_post_id,next_result[0],next_result[1]

    yield last_id,last_text,last_imgs

gen = post_data_generator(postgres_db_url)

from PIL import Image,ImageTk
import io
import matplotlib.pyplot as plt
import numpy as np
import tkinter

quit = False
while not quit:
    try:
        post_id,post_title,image_data = next(gen)
    except StopIteration:
        break
    root = tkinter.Tk()

    title_var = tkinter.StringVar()
    title_var.set(post_title)
    panel_title = tkinter.Label(root, 
        textvariable=title_var,
        font=("Arial", 25),
        width=50,
        wraplength=512,
        justify=tkinter.CENTER,
    )
    panel_title.pack()
    if len(image_data) > 0:
        img = ImageTk.PhotoImage(Image.open(io.BytesIO(image_data[0])).resize((512, 512)))
        panel = tkinter.Label(root, image=img, height=512, width=512)
        panel.pack(fill = "both")

    def button_callback(cls):
        root.destroy()

    def quit_callback():
        global quit
        quit = True
        root.destroy()

    c0_button = tkinter.Button(root,
        text="Class 0",
        command=lambda: button_callback(0),
    )
    c1_button = tkinter.Button(root,
        text="Class 1",
        command=lambda: button_callback(1),
    )
    quit_button = tkinter.Button(root,
        text="Quit",
        command=quit_callback,
    )
    c0_button.pack()
    c1_button.pack()
    quit_button.pack()

    print(post_id)
    root.mainloop()