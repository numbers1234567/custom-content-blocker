from typing import Dict
import time

import random
import requests
import json

from functools import cache

from data_models import *
from env import *
from rpc import *

class Session:
    def __init__(self, timeout : int=60*60):
        self.create_time = time.time()
        self.last_action_time = self.create_time
        self.timeout = timeout
        
    def get_curated_posts(self, posts_before, curation_mode, count_max=10, count_min=5, min_score=0.5) -> CuratedPostBatch:
        curated_posts : list[CuratedPost] = []

        social_posts = get_recent_posts(posts_before, count_max)

        # Score each post
        for post in social_posts:
            html_embed = post["html"]
            create_utc = post["create_utc"]
            post_id = post["post_id"]

            curation_scores = get_curate_score(post_id, curation_mode)

            curated_posts.append(
                CuratedPost(post_id=post_id, create_utc=create_utc, html=html_embed, curate_score=curation_scores)
            )

        # Sort descending by score
        curated_posts = sorted(curated_posts, key=lambda x : -x.curate_score)
        for idx,post in enumerate(curated_posts):
            if post.curate_score < min_score and idx >= count_min: 
                curated_posts = curated_posts[:idx]
                break

        return CuratedPostBatch(posts=curated_posts)
    
    def create_curation_mode(self, mode_name : str, preset_key : str|None) -> CurationMode:
        pass
    
class SessionUser(Session):
    def __init__(self, email : str, timeout : int=60*60):
        super().__init__(timeout)
        self.email = email


class SessionManager:
    def __init__(self, default_sessions:Dict[str, Session]={}):
        # identifier : Session
        self.sessions : Dict[str, Session] = default_sessions.copy()

    def register_session(self, identifier : str, session : Session):
        self.sessions[identifier] = session

    def __str__(self):
        return f"SessionUser {id(self)}: {len(self)}"
    
    def __len__(self):
        return len(self.sessions)

    def __getitem__(self, identifier) -> Session:
        return self.sessions[identifier]
    
    def __contains__(self, identifier) -> bool:
        return identifier in self.sessions