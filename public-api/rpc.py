from typing import Dict
import time

import random
import requests
import json

from functools import cache

@cache
def get_recent_posts(before : int, count : int=20):
    # Query post db
    response = requests.get(f"{POST_DB_MANAGER}/recent_posts?before={before}&count={count}")
    html_embeds = json.loads(response.content)["html_embeds"]
    
    return html_embeds

def url_encode(arg : str):
    return arg.replace(":", "%3A").replace("/", "%2F")

def get_curate_score(post_id : str, curation_key : str) -> float:
    if curation_key=="half":
        return random.random()
    if curation_key=="all":
        return 1
    if curation_key=="no_politics":
        try:
            response = requests.get(f"{CURATOR}/get_curate_score?post_id={url_encode(post_id)}&curate_key=no_politics")
        except Exception as e:
            print(f"[ERROR]: Failed to retrieve curate score for post_id {post_id} and curate_key {curation_key}")
            print("   Error Message: " + str(e))
            return 1
        try:
            result = float(response.content)
        except Exception as e:
            print(f"[ERROR]: Could not convert response score to float.")
            print("   Error Message: " + str(e))

        # Clamp result
        return max(min(result, 1), 0)