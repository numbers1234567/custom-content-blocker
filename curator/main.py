###############
#   IMPORTS   #
###############

# API
from fastapi import FastAPI,HTTPException
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel

# utility
import os

from pydantic import BaseModel
from typing import List,Union,Tuple,Iterable

import json
import requests

from functools import cache

import multiprocessing as mp
import asyncio
import time

import random

from backend_shared.data_models_http import *

# Data Processing
import numpy as np
from torch import nn
from torch.nn import CrossEntropyLoss
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


##########################
#   BACKGROUND PROCESS   #
##########################


def create_formatted_str_array(arr : Iterable[any]) -> str:
    return "{" + ",".join([str(i) for i in arr]) + "}"

def create_blip_head(curate_id : int):
    try: conn = psycopg2.connect(POSTGRES_DB_URL)
    except: raise Exception("Failed to connect to DB")
    # Initialize parameters
    stdv1 = 1. / np.sqrt(768)
    stdv2 = 1. / np.sqrt(10)

    w1,b1 = np.random.rand(768, 10)*(2*stdv1) - stdv1, np.random.rand(10)*(2*stdv1) - stdv1
    w2,b2 = np.random.rand(10, 2)*(2*stdv2) - stdv2, np.random.rand(2)*(2*stdv2) - stdv2
    
    # Biased initialization
    b2 = np.log([0.9, 0.1])

    # Insert
    try:
        cur = conn.cursor()
        cur.execute("""
            INSERT INTO blip_curation_heads (curation_id,weight1,weight2,bias1,bias2)
            VALUES (%s, %s, %s, %s, %s);
        """, (curate_id, 
              create_formatted_str_array([create_formatted_str_array(row) for row in w1]), 
              create_formatted_str_array([create_formatted_str_array(row) for row in w2]),
              create_formatted_str_array(b1),
              create_formatted_str_array(b2)))
        conn.commit()
        cur.close()
    except Exception as e:
        print(f"[ERROR]: Failed to insert BLIP head.")
        print("   Message: " + str(e))
        raise Exception("Failed to insert BLIP head")

def _bg_populate_curate_modes():
    last_iter = time.time()
    while True:
        try:
            conn = psycopg2.connect(POSTGRES_DB_URL)
            cur = conn.cursor()
            cur.execute("""
                SELECT curation_modes.curation_id
                FROM curation_modes LEFT JOIN blip_curation_heads ON curation_modes.curation_id=blip_curation_heads.curation_id
                WHERE create_utc >= %s AND weight1 IS NULL;
            """, (last_iter,))
            query_res = cur.fetchone()
            while query_res != None:
                c_id, = query_res
                try:
                    create_blip_head(curate_id=c_id)
                except Exception as e:
                    print(f"[ERROR]: Failed to create BLIP head for curate id {c_id}")
                    print("   Message: " + str(e))

                query_res = cur.fetchone()

            cur.close()
            conn.close()
        except Exception as e:
            print("[ERROR]: Unexpected exception")
            print("   Message: " + str(e))
        last_iter = time.time()
        time.sleep(1)

bg_worker_populate_mode = mp.Process(target=_bg_populate_curate_modes).start()


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

# Weight, Bias
LinearLayer = Tuple[np.array, np.array]
def get_blip_params(curate_key : str) -> Union[Tuple[LinearLayer, LinearLayer],None]:
    try:
        conn = psycopg2.connect(POSTGRES_DB_URL)
    except:
        raise HTTPException(status_code=500, detail="Failed to connect to database. Check credentials")

    try:
        cur = conn.cursor()
        cur.execute("""
            SELECT weight1,weight2,bias1,bias2 FROM blip_curation_heads
            WHERE curation_id IN (
                SELECT curation_id FROM curation_modes WHERE curation_key=%s
            );
        """, (curate_key, ))
        result = cur.fetchone()
    except:
        raise HTTPException(status_code=500, detail="Failed to query database.")
    if result==None:
        raise HTTPException(status_code=400, detail=f"Curation key {curate_key} does not exist.")
    weight1,weight2,bias1,bias2 = result
    
    weight1,weight2,bias1,bias2 = \
        [[float(i) for i in row] for row in weight1], \
        [[float(i) for i in row] for row in weight2], \
        [float(i) for i in bias1], \
        [float(i) for i in bias2]
    weight1,weight2,bias1,bias2 = np.array(weight1),np.array(weight2),np.array(bias1),np.array(bias2)
    weight1 = np.transpose(weight1, (1,0))
    weight2 = np.transpose(weight2, (1,0))
    return ((weight1, bias1), (weight2, bias2))

def update_blip_params(curate_key : str, params : BLIPParams):
    try:
        conn = psycopg2.connect(POSTGRES_DB_URL)
    except:
        raise Exception("Failed to connect to database.")
    
    cur = conn.cursor()
    cur.execute("""
        UPDATE blip_curation_heads
        SET weight1=%s,weight2=%s,bias1=%s,bias2=%s
        WHERE curation_id in (
            SELECT curation_id FROM curation_modes WHERE curation_key=%s
        );
    """, (create_formatted_str_array([create_formatted_str_array(row) for row in params.weight1]), 
        create_formatted_str_array([create_formatted_str_array(row) for row in params.weight2]),
        create_formatted_str_array(params.bias1),
        create_formatted_str_array(params.bias2),
        curate_key)
    )
    conn.commit()
    cur.close()
    conn.close()

@cache
def get_post_blip_features(post_id : str) -> Union[np.array,None]:
    try:
        conn = psycopg2.connect(POSTGRES_DB_URL)
        cur = conn.cursor()
    except:
        print("[ERROR]: Failed to connect to Postgres database. Check credentials.")
        return None

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
                );
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
politics_head.load_state_dict(torch.load("models/blip_deep_mlp_4_e5", map_location=torch.device("cpu")))
politics_head.eval()

def load_blip_head(curate_key : str) -> BLIPHead|None:
    params = get_blip_params(curate_key)
    if params is None:
        print(f"[ERROR]: Could not find parameters for curate_key {curate_key}!")
        return None
    
    l1, l2 = params
    head = BLIPHead()
    head.mlp[0].weight = nn.Parameter(torch.Tensor(l1[0]).type(torch.float32))
    head.mlp[0].bias = nn.Parameter(torch.Tensor(l1[1]).type(torch.float32))
    head.mlp[3].weight = nn.Parameter(torch.Tensor(l2[0]).type(torch.float32))
    head.mlp[3].bias = nn.Parameter(torch.Tensor(l2[1]).type(torch.float32))

    head.eval()

    return head

def get_blip_curate_score(post_id : str, curate_key : str) -> float|None:
    if curate_key=="half":
        return random.random()
    if curate_key=="all":
        return 1
    
    features = get_post_blip_features(post_id)

    if features is None:
        print(f"[LOG]: No BLIP features for {post_id}")
        return None
    
    head = load_blip_head(curate_key=curate_key)
    if not head:
        print(f"[LOG]: No BLIP head for {curate_key}")
        return None
    
    with torch.no_grad():
        features = torch.from_numpy(features).unsqueeze(0).type(torch.float32)

        result = head(features).cpu().detach().numpy()[0]
    return result[0]/(result[0]+result[1])

@app.get("/get_curate_score")
async def get_curate_score(post_id : str, curate_key : str) -> float:
    blip_score = get_blip_curate_score(post_id, curate_key)
    return blip_score if blip_score else 1

def update_blip_head(curate_key : str, post_id : str, positive : bool):
    head = load_blip_head(curate_key)
    if head is None:
        return
    head.train()
    features = get_post_blip_features(post_id)
    if features is None:
        return
    
    # Train
    optimizer = torch.optim.Adam(head.parameters())
    features = torch.from_numpy(features).unsqueeze(0).type(torch.float32)
    label = [[1,0]] if positive else [[0,1]]
    label = torch.tensor(label).type(torch.float32)
    loss = CrossEntropyLoss()
    l = torch.mean(loss(head(features), label))
    l.backward()
    optimizer.step()

    # Store new parameters
    w1 = head.mlp[0].weight.cpu().detach().numpy()
    w2 = head.mlp[3].weight.cpu().detach().numpy()
    b1 = head.mlp[0].bias.cpu().detach().numpy()
    b2 = head.mlp[3].bias.cpu().detach().numpy()
    w1 = np.transpose(w1, (1,0))
    w2 = np.transpose(w2, (1,0))
    new_params = BLIPParams(
        weight1=[list(i) for i in w1],
        weight2=[list(i) for i in w2],
        bias1=list(b1),
        bias2=list(b2),
    )

    update_blip_params(curate_key, new_params)
    

@app.post("/recommend_post")
async def recommend_post(request : RecommendPostRequestBody) -> RecommendPostResponseBody:
    curate_key, post_id, positive = request.curate_key, request.post_id, request.options.positive
    
    update_blip_head(curate_key, post_id, positive)

    return RecommendPostResponseBody()