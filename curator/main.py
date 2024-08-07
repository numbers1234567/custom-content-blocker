###############
#   IMPORTS   #
###############

# API
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

# utility
import os

from pydantic import BaseModel
from typing import List,Union

import json
import requests

from functools import cache

import multiprocessing as mp
import asyncio
import time

import random

# Data Processing
import numpy as np
from torch import nn
import torch

# Database
import psycopg2


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

@cache
def get_post_blip_features(post_id : str) -> Union[np.array,None]:
    try:
        conn = psycopg2.connect(POSTGRES_DB_URL)
        cur = conn.cursor()
    except:
        print("[ERROR]: Failed to connect to Postgres database. Check credentials.")

    try:
        # Get post's BLIP features
        cur.execute("""
            SELECT features
            FROM blip_features as b
            WHERE b.internal_id IN
                (
                SELECT s.internal_id
                FROM social_post_data as s
                WHERE s.post_id LIKE %s
                )
        """, (post_id,))
    except Exception as e:
        print("[ERROR]: Failed to query for BLIP features.")
        print("   Message: " + str(e))

        return None

    features = cur.fetchone() # (features, ) or None

    # Post does not have BLIP features.
    if not features:
        return None

    return np.array([float(feature) for feature in features[0]])


class BLIPHead(nn.Module):
    # BlipDeepHead4
    def __init__(self, device="cpu"):
        super().__init__()
        seq = [
            nn.Linear(768, 10),
            nn.ReLU(),
            nn.Dropout(p=0.2),
            nn.Linear(10, 2),
            nn.Sigmoid()
        ]
        self.mlp = nn.Sequential(
            *seq
        ).to(device)

    def forward(self, features):
        return self.mlp(features)

politics_head = BLIPHead()
politics_head.load_state_dict(torch.load("blip_deep_mlp_4_e5", map_location=torch.device("cpu")))
politics_head.eval()

@cache
def get_blip_curate_score(post_id : str, curate_key : str) -> float:
    if curate_key=="half":
        return random.random()
    if curate_key=="all":
        return 1
    if curate_key=="no_politics":
        features = get_post_blip_features(post_id)

        if features is None:
            return 1
        with torch.no_grad():
            features = torch.from_numpy(features).unsqueeze(0).type(torch.float32)

            result = politics_head(features).cpu().detach().numpy()[0]
        return result[0]/(result[0]+result[1])
    
    return 1

@app.get("/get_curate_score")
async def get_curate_score(post_id : str, curate_key : str) -> float:
    return get_blip_curate_score(post_id, curate_key)

if __name__=="__main__":
    # Some unit tests here

    # no_politics mode:
    print("==TESTING no_politics MODE==")
    # My opinion:
    test_posts = [
        "https://www.reddit.com/r/iamatotalpieceofshit/comments/1el50gq/guy_pushes_his_girlfriend_into_a_lake/",
        "https://www.reddit.com/r/pics/comments/1el4jr7/jd_vance_beardless/",
        "https://www.reddit.com/r/AnythingGoesNews/comments/1el4iqj/kamala_harris_hits_record_lead_over_trump_new/",
        "https://www.reddit.com/r/Damnthatsinteresting/comments/1el3yv4/a_horse_protecting_his_owner_from_a_cow_whilst_he/",
        "https://www.reddit.com/r/interestingasfuck/comments/1el3q1k/republican_mayor_of_mesa_arizona_my_city_would/",
        "https://www.reddit.com/r/news/comments/1el3fdh/multiple_athletes_hospitalised_after_paris/",
        "https://www.reddit.com/r/todayilearned/comments/1el3f1f/til_michael_phelps_has_won_a_record_23_olympic/",
        "https://www.reddit.com/r/politics/comments/1el2pee/jd_vance_falsely_accuses_algerian_olympic_boxer/",
        "https://www.reddit.com/r/FluentInFinance/comments/1el2nee/folks_like_this_are_why_finacial_literacy_is_so/",
        "https://www.reddit.com/r/antiwork/comments/1el2mbl/this_is_the_biggest_bootlicking_post_ive_ever_seen/",
    ]
    angelo_expectation = [
        False,
        False,
        True,
        False,
        True,
        False,
        False,
        True,
        False,
        False,
    ]
    for test_post,expect in zip(test_posts, angelo_expectation):
        print(f"{test_post} ({expect}) : {get_blip_curate_score(test_post, 'no_politics')}")
        
    print("==FINISH no_politics TEST==")