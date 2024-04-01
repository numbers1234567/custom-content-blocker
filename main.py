from fastapi import FastAPI, HTTPException, List
from pydantic import BaseModel

class PostInfo(BaseModel):
    post_id : str
    text : str
    media_urls : list[str] = []


app = FastAPI()


@app.post("/process_post/{user_key}")
def process_post(user_key : str, post_info : PostInfo):
    return {"message" : "bruh"}

@app.post("/blocked_post/{user_key}")
def block_post(user_key : str, id : str):
    return 