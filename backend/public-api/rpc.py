from typing import Dict
import time

import random
import requests
import json

from backend_shared.data_models import *

from .env import *

from functools import cache

@cache
def get_recent_posts(before : int, count : int=20) -> GetRecentPostsResponseBody:
    # Query post db
    response = requests.get(f"{POST_DB_MANAGER}/recent_posts?before={before}&count={count}")
    
    return GetRecentPostsResponseBody.model_validate(json.loads(response.content))

def url_encode(arg : str):
    return arg.replace(":", "%3A").replace("/", "%2F")

def get_curate_score(post_id : str, curation_key : str) -> float:
    if curation_key=="half":
        return random.random()
    if curation_key=="all":
        return 0
    try:
        response = requests.get(f"{CURATOR}/get_curate_score?post_id={url_encode(post_id)}&curate_key={curation_key}")
    except Exception as e:
        print(f"[ERROR]: Failed to retrieve curate score for post_id {post_id} and curate_key {curation_key}")
        print("   Error Message: " + str(e))
        return 0
    try:
        result = float(response.content)
    except Exception as e:
        print(f"[ERROR]: Could not convert response score to float.")
        print("   Error Message: " + str(e))

    # Clamp result
    return max(min(result, 1), 0)
    
def get_user_data(email : str) -> GetUserDataResponseBody|None:
    response = requests.post(f"{POST_DB_MANAGER}/get_user_data", json={
        "email" : email
    })
    
    if response.status_code < 200 or response.status_code > 299:
        return None
    
    return GetUserDataResponseBody.model_validate(json.loads(response.content))
    
def sign_up_user_db_manager(email : str):
    response = requests.post(f"{POST_DB_MANAGER}/sign_up_user", json={
        "credentials" : {
            "email" : email
        }
    })

    return (response.status_code >= 200 and response.status_code <= 299, response.status_code)

def create_curation_mode(email : str, curation_name : str) -> CreateCurationModeResponseBody:
    response = requests.post(f"{POST_DB_MANAGER}/create_curation_mode",
        json={"credentials" : {"email" : email}, "mode_name" : curation_name}
    )

    return CreateCurationModeResponseBody.model_validate(json.loads(response.content))

def delete_curation_mode(curation_key : str) -> DeleteCurationModeResponseBody:
    response = requests.post(f"{POST_DB_MANAGER}/delete_curation_mode",
        json={"curation_key" : curation_key}
    )

    return DeleteCurationModeResponseBody.model_validate(json.loads(response.content))

def get_emerging_topics(from_time: int, to_time: int|None) -> List[CurationMode]:
    if to_time==None:
        to_time = int(time.time())
    
    uri = f"{CURATOR}/emerging_topics?from_time={from_time}&to_time={to_time}" if to_time!=None else f"{CURATOR}/emerging_topics?from_time={from_time}"

    response = requests.get(uri)

    return [CurationMode.model_validate(topic) for topic in json.loads(response.content)]

def recommend_post(post_id : str, curate_key : str, positive : bool) -> RecommendPostResponseBody:
    response = requests.post(f"{CURATOR}/recommend_post",
        json={"curate_key" : curate_key, "post_id" : post_id, "options" : {"positive" : positive}}
    )

    return RecommendPostResponseBody.model_validate(json.loads(response.content))