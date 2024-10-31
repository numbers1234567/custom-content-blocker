from typing import Dict
import time

from typing import List

from functools import cache

from .env import *
from .rpc import CuratedPostBatch, CuratedPost, get_curate_score,CurationMode,Credentials,recommend_post,get_emerging_topics

from backend_shared.data_models import EmergingTopic,EmergingTopicList
from backend_shared.data_store import DataStorePost,DataStoreUser,UserData

from .authenticator import Authenticator

from threading import Lock,Thread

class Session:
    def __init__(self, data_store_post: DataStorePost, data_store_user: DataStoreUser, timeout : int=1e12):
        self.create_time = time.time()
        self.last_action_time = self.create_time
        self.timeout = timeout

        self.data_store_post: DataStorePost = data_store_post
        self.data_store_user: DataStoreUser = data_store_user
        
    def get_curated_posts(self, posts_before, curation_mode, count_max=10, count_min=5, max_score=0.5) -> CuratedPostBatch:
        self.last_action_time = time.time()
        curated_posts : list[CuratedPost] = []

        social_posts = self.data_store_post.get_recent_posts(posts_before, count=count_max)

        # Score each post
        for post in social_posts:
            html_embed = post.embed_html
            create_utc = post.create_utc
            post_id = post.post_id

            curation_scores = get_curate_score(post_id, curation_mode)

            curated_posts.append(
                CuratedPost(post_id=post_id, create_utc=create_utc, html=html_embed, curate_score=curation_scores)
            )

        # Sort ascending by score
        curated_posts = sorted(curated_posts, key=lambda x : x.curate_score)
        for idx,post in enumerate(curated_posts):
            if post.curate_score > max_score and idx >= count_min: 
                curated_posts = curated_posts[:idx]
                break

        return CuratedPostBatch(posts=curated_posts)
    
    def get_usable_curate_modes(self) -> List[CurationMode]:
        self.last_action_time = time.time()
        return [CurationMode(key="all", name="All"), CurationMode(key="no_politics", name="No Politics"), CurationMode(key="politics_only", name="Politics Only")]
    
    def expired(self) -> bool:
        return time.time()-self.last_action_time > self.timeout
    
    def get_emerging_topics(self) -> List[EmergingTopic]:
        return []
    
    
# An authenticated session
class SessionUser(Session):
    current_emerging_topics: List[EmergingTopic] = []
    emerging_topics_lock: Lock = Lock()
    update_period: int = 24*60*60
    last_update_time: int = 0
    def __init__(self, data_store_post: DataStorePost, data_store_user: DataStoreUser, email : str, timeout : int=60*60):
        super().__init__(data_store_post=data_store_post, data_store_user=data_store_user, timeout=timeout)
        self.email = email
        
        try:
            self.user_data: UserData = self.data_store_user[email]

        except ValueError:
            self.user_data: UserData = self.data_store_user.create_user(email, return_user=True)

        self.curate_mode_limit = 10  # Current default
        self.curate_modes: List[CurationMode] = []

        self.timeout = timeout
    
    def create_curation_mode(self, mode_name : str) -> CurationMode | None:
        if len(self.curate_modes) >= 10:
            return None
        curate_data = self.user_data.create_curation_mode(mode_name)

        self._refresh()

        return curate_data.curation_mode
    
    def delete_curation_mode(self, curation_key : str):
        if curation_key not in [i.key for i in self.curate_modes]:
            return False
        self.user_data.delete_curation_mode(curation_key)
        
        self._refresh()
        return True
    
    def get_usable_curate_modes(self) -> List[CurationMode]:
        return super().get_usable_curate_modes() + self.curate_modes

    def recommend_post(self, curate_key : str, post_id : str, positive : str):
        if curate_key not in [i.key for i in self.curate_modes]:
            return False
        
        recommend_post(post_id, curate_key, positive)

        return True
    
    def get_emerging_topics(self, from_time: int, to_time: int|None=None) -> List[EmergingTopic]:
        if time.time() - SessionUser.last_update_time > SessionUser.update_period:
            with SessionUser.emerging_topics_lock:
                SessionUser.current_emerging_topics = get_emerging_topics(from_time, to_time)
                SessionUser.last_update_time = int(time.time())
        
        return SessionUser.current_emerging_topics
    
    def _refresh(self):
        self.user_data.refresh()

        self.curate_mode_limit = 10  # Current default

class SessionManager:
    def __init__(self, data_store_post: DataStorePost, data_store_user: DataStoreUser, authenticator:Authenticator=Authenticator(), default_sessions:Dict[str, Session]={}):
        # identifier : Session
        self.session_registry_lock = Lock()
        self.sessions : Dict[str, Session] = default_sessions.copy()
        self.authenticator=authenticator
        self.max_sessions = 1000

        self.data_store_post = data_store_post
        self.data_store_user = data_store_user

    def login(self, credentials:Credentials):
        token = credentials.token
        if token in self:
            return False
        
        try:
            user_data = self.authenticator.authenticate(credentials)
        except Exception as e:
            return False

        self.register_session(token, SessionUser(self.data_store_post, self.data_store_user, user_data.email))
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