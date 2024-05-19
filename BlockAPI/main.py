import time
import base64

# API
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

import net_msg
import post_data

from client_manager import ClientManager

origins = [
]

app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)

mgr = ClientManager()

def decode_b64media(media : str) -> bytes:
    return base64.b64decode(media)

def package_data(user_key : str, post_info : net_msg.PostData) -> post_data.PostData:
    video_data = []
    image_data = []
    text = post_info.media.text
    crt_time = time.time()

    for video in post_info.media.video:
        video_data.append(post_data.Media(content=decode_b64media(video.content), data_format=video.dataFormat))
    for image in post_info.media.images:
        image_data.append(post_data.Media(content=decode_b64media(image.content), data_format=image.dataFormat))
    
    metadata = post_data.Metadata(ukey=user_key, uid=post_info.metadata.id, crt_time=crt_time)
    media_data = post_data.MediaData(text=text, images=image_data, video=video_data)

    return post_data.PostData(media=media_data, metadata=metadata)

def get_block_result(data : post_data.PostData):
    return mgr.block_score(data).item()

@app.post("/process_post/{user_key}/")
async def process_post(user_key : str, post_info : net_msg.PostData):
    data = package_data(user_key, post_info)
    res = get_block_result(data)
    print(type(res))
    return {"block_score" : res}

@app.post("/blocked_post/{user_key}")
async def block_post(user_key : str, id : str):
    return 