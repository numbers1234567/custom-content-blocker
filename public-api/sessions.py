from typing import Dict
import time

import random
import requests
import json

from functools import cache

from .env import *
from .rpc import *

from .authenticator import Authenticator

from threading import Lock

class Session:
    def __init__(self, timeout : int=1e12):
        self.create_time = time.time()
        self.last_action_time = self.create_time
        self.timeout = timeout
        
    def get_curated_posts(self, posts_before, curation_mode, count_max=10, count_min=5, min_score=0.5) -> CuratedPostBatch:
        self.last_action_time = time.time()
        curated_posts : list[CuratedPost] = []

        social_posts = get_recent_posts(posts_before, count_max)

        # Score each post
        for post in social_posts.html_embeds:
            html_embed = post.html
            create_utc = post.create_utc
            post_id = post.post_id

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
    
    def get_usable_curate_modes(self) -> List[CurationMode]:
        self.last_action_time = time.time()
        return [CurationMode(key="all", name="All"), CurationMode(key="no_politics", name="No Politics"), CurationMode(key="politics_only", name="Politics Only")]
    
    def expired(self) -> bool:
        return time.time()-self.last_action_time > self.timeout
    
    
# An authenticated session
class SessionUser(Session):
    def __init__(self, email : str, timeout : int=60*60):
        super().__init__(timeout)
        self.email = email
        
        user_data = get_user_data(email)
        if user_data==None:
            if not self.sign_up_user():
                raise ValueError(f"Failed to create user {email}.")
            user_data = get_user_data(email)
        self.signup_time = user_data.create_utc
        self.curate_modes = user_data.curate_modes

        self.curate_mode_limit = 10  # Current default

        self.timeout = timeout

    def sign_up_user(self) -> bool:
        success, status = sign_up_user_db_manager(self.email)
        return success
    
    def create_curation_mode(self, mode_name : str) -> CurationMode | None:
        if len(self.curate_modes) >= 10:
            return None
        curate_data = create_curation_mode(self.email, mode_name)

        self._refresh()

        return curate_data.curation_mode
    
    def delete_curation_mode(self, curation_key : str):
        if curation_key not in [i.key for i in self.curate_modes]:
            return False
        delete_curation_mode(curation_key)
        
        self._refresh()
        return True
    
    def get_usable_curate_modes(self) -> List[CurationMode]:
        return super().get_usable_curate_modes() + self.curate_modes

    def recommend_post(self, curate_key : str, post_id : str, positive : str):
        if curate_key not in [i.key for i in self.curate_modes]:
            return False
        
        recommend_post(post_id, curate_key, positive)

        return True
    
    def _refresh(self):
        user_data = get_user_data(self.email)
        self.signup_time = user_data.create_utc
        self.curate_modes = user_data.curate_modes

        self.curate_mode_limit = 10  # Current default

class SessionManager:
    def __init__(self, authenticator:Authenticator=Authenticator(), default_sessions:Dict[str, Session]={}):
        # identifier : Session
        self.session_registry_lock = Lock()
        self.sessions : Dict[str, Session] = default_sessions.copy()
        self.authenticator=authenticator
        self.max_sessions = 1000

    def login(self, credentials:Credentials):
        token = credentials.token
        if token in self:
            return False
        
        try:
            user_data = self.authenticator.authenticate(credentials)
        except Exception as e:
            return False

        self.register_session(token, SessionUser(user_data.email))
        return True

    def register_session(self, identifier : str, session : Session):
        with self.session_registry_lock:
            if len(self.sessions) >= self.max_sessions:
                for id_,session in self.sessions:
                    if session.expired():
                        del self.sessions[id_]
            self.sessions[identifier] = session

    def __str__(self):
        return f"SessionUser {id(self)}: {len(self)}"
    
    def __len__(self):
        return len(self.sessions)

    def __getitem__(self, identifier) -> Session:
        return self.sessions[identifier]
    
    def __contains__(self, identifier) -> bool:
        return identifier in self.sessions