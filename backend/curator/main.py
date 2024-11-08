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

import threading
import asyncio
import time

import random

import re

from backend_shared.data_models import *
from backend_shared.data_store import *

# Data Processing
import numpy as np
from torch import nn
from torch.nn import CrossEntropyLoss
import torch

from .background_ml import NGramDFWorker
from sklearn.feature_extraction.text import CountVectorizer

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

n_gram_freq_worker = NGramDFWorker(POSTGRES_DB_URL, verbose=True)
n_gram_freq_worker.start()

data_store_post = DataStorePost(POSTGRES_DB_URL, verbose=True)

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

@cache
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

@cache
def get_blip_curate_score(post_id : str, curate_key : str) -> float|None:
    if curate_key=="half":
        return random.random()
    if curate_key=="all":
        return 0
    
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
    return result[1]/(result[0]+result[1])

@cache
def get_restricted_ngram_helper(key: str):
    with psycopg2.connect(POSTGRES_DB_URL) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT ngram
            FROM emerging_topic NATURAL JOIN emerging_topic_ngram
            WHERE topic_key=%s;
        """, (key,))

        result = cur.fetchall()
        cur.close()
        return [ngram for ngram, in result]
    
@cache
def get_restricted_regex_helper(key: str) -> re.Pattern:
    with psycopg2.connect(POSTGRES_DB_URL) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT regex
            FROM emerging_topic NATURAL JOIN emerging_topic_regex
            WHERE topic_key=%s;
        """, (key,))

        result = cur.fetchone()
        cur.close()

        r_pattern = result[0]
        return re.compile(r_pattern)

def get_restricted_ngram(topic : CurationMode) -> List[str]:
    return get_restricted_ngram_helper(topic.key)

# I feel this isn't very testable. Look at those inner functions. I did this because I didn't want to pollute the namespace.
def get_ensembled_curate_score(post_id : str, curation_setting : CurationSetting) -> float:
    # I/O heavy operations

    # result_buffer stores results
    result_buffer_lock = threading.Lock()
    result_buffer: List[float] = [0] * 3
    BLIP_IDX  = 0
    NGRAM_IDX = 1
    REGEX_IDX = 2
    def blip_worker(post_id : str, curate_key : str, result_buf: List[float], result_idx: int):
        score = get_blip_curate_score(post_id,curate_key)
        score: float = score if score else 0


        with result_buffer_lock:
            result_buf[result_idx] = score

    def ngram_worker(post_id : str, filters : List[CurationMode], result_buf: List[float], result_idx: int):
        vectorizer = CountVectorizer(ngram_range=(1,7))
        vectorizer.fit([data_store_post[post_id].text])

        post_ngrams = vectorizer.get_feature_names_out()
        with result_buffer_lock:
            result_buf[result_idx] = 0
        
        for filter in filters:
            try:
                restricted = get_restricted_ngram_helper(filter.key)
            except Exception as e:
                print("[ERROR]: Failed to retrieve n-gram helper.")
                print("   Message: " + str(e))
                continue
            
            if len(restricted) == 0:
                continue
            works = True
            for ngram in restricted:
                if ngram not in post_ngrams:
                    works=False

            if works:
                with result_buffer_lock:
                    result_buf[result_idx] = 1
                break

    def regex_worker(post_id: str, filters: List[CurationMode], result_buf: List[float], result_idx: int):
        
        text = data_store_post[post_id].text.lower()

        # Keep only alphanumeric characters
        text = re.sub("[^a-zA-Z0-9]", " ", text)

        with result_buffer_lock:
            result_buf[result_idx] = 0

        for filter in filters:
            try:
                pattern = get_restricted_regex_helper(filter.key)
            except Exception as e:
                print("[ERROR]: Failed to retrieve regex helper.")
                print("   Message: " + str(e))
                continue

            # If the post matches a pattern, filter it out.
            if pattern.match(text):
                with result_buffer_lock:
                    result_buf[result_idx] = 1
                return

    blip_thread = threading.Thread(target=blip_worker, 
                                   args=(post_id, curation_setting.curation_mode.key, result_buffer,BLIP_IDX))
    ngram_thread = threading.Thread(target=ngram_worker,
                                    args=(post_id, curation_setting.trending_filters, result_buffer, NGRAM_IDX))
    regex_thread = threading.Thread(target=regex_worker,
                                    args=(post_id, curation_setting.trending_filters, result_buffer, REGEX_IDX))
    
    blip_thread.start()
    ngram_thread.start()
    regex_thread.start()

    blip_thread.join()
    ngram_thread.join()
    regex_thread.join()

    if result_buffer[NGRAM_IDX] >= 0.5 or result_buffer[REGEX_IDX] >= 0.5: return 1
    else: return result_buffer[BLIP_IDX]


@app.post("/get_curate_score")
async def get_curate_score(request : GetCurateScoreRequestBody) -> GetCurateScoreResponseBody:
    if request.post_id==None and request.post_ids==None:
        raise HTTPException(status_code=400, detail="Provide either a post_id or a list of post_ids")
    
    post_ids : List[str] = request.post_ids if request.post_ids != None else [request.post_id]

    scores_lock = threading.Lock()
    scores : List[PostScore] = [PostScore(score=-1e9, post_id=post_id, success=False) for post_id in post_ids]

    def process_post(post_id : str, curation_setting : CurationSetting, scores_buffer : List[float], scores_idx : int):
        try:
            score = PostScore(score=get_ensembled_curate_score(post_id, curation_setting), post_id=post_id, success=True)
            with scores_lock:
                scores[scores_idx] = score
        except Exception as e:
            print(f"[ERROR]: Failed to curate post {post_id}.")
            print("   Message: " + str(e))

    threads: List[threading.Thread] = []
    for i,post_id in enumerate(post_ids):
        thread = threading.Thread(target=process_post,
                                  args=(post_id, request.curation_settings, scores, i))
        thread.start()
        threads.append(thread)
    
    for thread in threads:
        thread.join()

    return GetCurateScoreResponseBody(scores=scores)
    

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

@app.get("/emerging_topics")
async def emerging_topics(from_time: int, to_time: int|None):
    if to_time==None:
        to_time = time.time()
    
    with psycopg2.connect(POSTGRES_DB_URL) as conn:
        cur = conn.cursor()
        cur.execute("""
            SELECT topic_name, topic_key
            FROM emerging_topic
            WHERE create_utc >= %s AND create_utc < %s;
        """, (from_time, to_time))
        result = cur.fetchall()
        return [CurationMode(name=name,key=key) 
                    for name,key in result]

@app.post("/recommend_post")
async def recommend_post(request : RecommendPostRequestBody) -> RecommendPostResponseBody:
    curate_key, post_id, positive = request.curate_key, request.post_id, request.options.positive
    
    update_blip_head(curate_key, post_id, positive)

    return RecommendPostResponseBody()