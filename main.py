from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import sys
sys.path.append("BLIP")

from models.blip import blip_feature_extractor


class PostInfo(BaseModel):
    post_id : str
    text : str
    media_urls : list[str] = []


app = FastAPI()


@app.post("/process_post/{user_key}/")
def process_post(user_key : str):
    return {"message" : "bruh"}

@app.post("/blocked_post/{user_key}")
def block_post(user_key : str, id : str):
    return 