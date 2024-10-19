import psycopg2
from dataclasses import dataclass,field

import random

from typing import List

from functools import cache
import threading

@dataclass
class SocialPostBaseMetaData:
    create_utc : int
    # Unique internal post ID which can be used to find the source
    post_id : str

@dataclass
class SocialPostBaseMediaData:
    embed_html : str = ""
    text : str = ""

@dataclass
class SocialPostBaseData:
    metadata   : SocialPostBaseMetaData
    media_data : SocialPostBaseMediaData

class DataStore:
    def __init__(self, postgres_db_url: str, verbose: bool=False):
        self.postgres_db_url = postgres_db_url
        self._verbose = verbose
        
    def _log(self, text: str, message:str|None = None):
        if not self._verbose: return
        print(f"[LOG-{self}]: {text}")
        if message:
            print(f"   Message: {message}")

    def create_db_connection(self):  # No type annotation, but should return a psycopg2 connection
        return psycopg2.connect(self.postgres_db_url)

class DataStorePost(DataStore):
    def __init__(self, postgres_db_url, verbose=False):
        super().__init__(postgres_db_url, verbose=verbose)

        self.max_id_lock = threading.Lock()
        self.max_id = 0
        self._set_max_id()

    def _set_max_id(self):
        with self.create_db_connection() as conn, self.max_id_lock:
            cur: psycopg2.cursor = conn.cursor()

            cur.execute("""
                SELECT MAX(internal_id)
                FROM social_post_data;
            """)

            result = cur.fetchone()

            self.max_id = result[0] if result[0]!=None else -1
            
            cur.close()

    def __contains__(self, post_id: str) -> bool:
        with self.create_db_connection() as conn:
            cur = conn.cursor()

            # Check if a post is fetched with the id
            cur.execute("""
                SELECT * 
                FROM social_post_data
                WHERE post_id=%s;
            """, (post_id, ))
            db_post = cur.fetchone()
            cur.close()

            return db_post != None
    
    def insert_post(self, post_id: str, embed_html: str, text: str, create_utc: int, _retries: int = 100):
        try:
            # This post "claims" add_id as its id
            with self.max_id_lock:
                add_id = self.max_id + 1
                self.max_id = max(add_id + 1, self.max_id)

            # Try to insert
            with self.create_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO social_post_data (internal_id, post_id, title, embed_html, create_utc) 
                        VALUES (%s, %s, %s, %s, %s);
                """, (add_id, post_id, text, embed_html, create_utc))

                conn.commit()
                cur.close()

                self._log(f"Successfully inserted post {post_id}")

        except psycopg2.IntegrityError as e:  # This should catch the max id being desynced for some reason
            self._log(f"Failed to insert post {post_id} with internal id {add_id}. Retries left: {_retries}.",
                        message=str(e))
            if _retries > 0:
                self._set_max_id()

                self.insert_post(post_id, embed_html, text, create_utc, _retries=_retries-1)


    def __getitem__(self, post_id: str) -> SocialPostBaseData:
        with self.create_db_connection() as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT * 
                FROM social_post_data
                WHERE post_id=%s;
            """, (post_id, ))

            result = cur.fetchone()
            if result==None:
                raise ValueError(f"Post {post_id} is not in the data store")

            internal_id, post_id, text, embed_html, create_utc = result
            cur.close()

            return SocialPostBaseData(
                metadata=SocialPostBaseMetaData(
                    create_utc=create_utc,
                    post_id=post_id,
                ),
                media_data=SocialPostBaseMediaData(
                    embed_html=embed_html,
                    text=text,
                ),
            )
    
    def get_recent_posts(self, before: int, count: int=20) -> List[SocialPostBaseData]:
        with self.create_db_connection() as conn:
            cur = conn.cursor()
            # New to SQL, so there might be a more performant way to do this.
            # There's also possibility for indexing
            cur.execute("""
                SELECT internal_id, post_id, title, embed_html, create_utc
                FROM social_post_data
                WHERE create_utc < %s
                ORDER BY create_utc DESC
                LIMIT %s;
            """, (before, count))
            result = cur.fetchall()
        
        return [
            SocialPostBaseData(
                metadata=SocialPostBaseMetaData(
                    create_utc=create_utc,
                    post_id=post_id,
                ),
                media_data=SocialPostBaseMediaData(
                    embed_html=embed_html,
                    text=text,
                ),
            )
            for internal_id, post_id, text, embed_html, create_utc in result
        ]
    
@dataclass
class CurationModeID:
    name: str
    key: str

class UserData(DataStore):
    # Curate id must be synced
    whitelist_key_characters = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
    max_curate_id_lock = threading.Lock()
    def _set_max_curate_id(postgres_db_url: str):
        with psycopg2.connect(postgres_db_url) as conn:
            cur = conn.cursor()
            
            cur.execute("""
                SELECT MAX(curation_id)
                FROM curation_modes;
            """)

            result = cur.fetchone()

            max_id = result[0] if result[0]!=None else -1
            
            cur.close()
            conn.close()

            UserData.max_curate_id = max_id
    max_curate_id = 0

    def __init__(self, postgres_db_url: str, email: str, create_utc: int=None, uid: int=None, curation_modes: List[CurationModeID]|None=None, verbose: bool = False):
        super().__init__(postgres_db_url, verbose=verbose)

        self.email: str = email
        self.create_utc: int = 0
        self.uid: int = -1

        self.curation_modes = []

        if create_utc: self.create_utc: int = create_utc
        if uid: self.uid: int = uid
        if curation_modes: self.curation_modes = curation_modes

        if not create_utc or not uid or not curation_modes: self.refresh()

    def refresh(self):
        with self.create_db_connection() as conn:
            cur = conn.cursor()


            try:
                # Credentials
                cur.execute("""
                    SELECT user_id, create_utc FROM user_credentials
                    WHERE email=%s;
                """, (self.email,))

                self.uid, self.create_utc = cur.fetchone()  # Handled exception - user does not exist

                # Curation modes
                cur.execute("""
                    SELECT curation_key,curation_name FROM curation_modes
                    WHERE primary_user=%s;
                """, (self.uid,))

                curation_modes = cur.fetchall()
                self.curation_modes = [CurationModeID(key=key, name=name) for key,name in curation_modes]

            except TypeError as e:
                self._log(f"Failed to retrieve data for {self}. Does the user exist in the database?",
                          message=str(e))
                

            cur.close()
    
    def create_curation_mode(self, name: str, _retries=100):
        create_utc = time.time()
        curation_key = "".join([random.choice(UserData.whitelist_key_characters) for _ in range(40)])
        
        # "Claim" this id
        with UserData.max_curate_id_lock:
            curation_id = UserData.max_curate_id + 1
            UserData.max_curate_id += 1

        try:
            with self.create_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    INSERT INTO curation_modes (primary_user, curation_id, curation_name, curation_key, create_utc) 
                    VALUES (%s, %s, %s, %s, %s);
                """, (self.uid, curation_id, name, curation_key, create_utc))

                conn.commit()
                cur.close()
        
        except psycopg2.IntegrityError as e:  # This should catch the max id being desynced for some reason or for the statistical anomaly of a taken key
            self._log(f"Failed to insert curation mode {name} with id {curation_id} and key {curation_key}. Retries left: {_retries}.",
                        message=str(e))
            if _retries > 0:
                UserData._set_max_curate_id(self.postgres_db_url)
                self.create_curation_mode(name, _retries=_retries-1)

    def __repr__(self):
        return f"User-{self.uid}:{self.email}"

class DataStoreUser(DataStore):
    def __init__(self, postgres_db_url, verbose=False):
        super().__init__(postgres_db_url, verbose=verbose)

        self.max_uid = -1
        self.max_uid_lock = threading.Lock()

    def _set_max_uid(self):
        with self.create_db_connection() as conn, self.max_uid_lock:
            cur: psycopg2.cursor = conn.cursor()

            cur.execute("""
                SELECT MAX(user_id)
                FROM user_credentials;
            """)

            result = cur.fetchone()

            self.max_uid = result[0] if result[0]!=None else -1
            
            cur.close()

    def create_user(self, email: str, return_user=False, _retries=100) -> UserData|None:
        create_time = time.time()
        with self.max_uid_lock:
            add_id = self.max_uid + 1
            self.max_uid += 1

        try:
            with self.create_db_connection() as conn:  # Insert user
                cur = conn.cursor()

                cur.execute("""
                    INSERT INTO user_credentials (user_id, create_utc, email)
                    VALUES (%s, %s, %s);
                """, (add_id, create_time, email))

                conn.commit()
                cur.close()

                if return_user: return UserData(self.postgres_db_url, email, create_utc=create_time, uid=add_id, curation_modes=[], verbose=self._verbose)

        except psycopg2.IntegrityError as e:  # This should catch the max id being desynced for some reason
            self._log(f"Failed to insert user {email} with id {add_id}. Retries left: {_retries}.",
                      message=str(e))
            
            if _retries > 0:
                self._set_max_uid()
                return self.create_user(email, return_user=return_user, _retries=_retries-1)
        

    def __getitem__(self, email: str) -> UserData:
        try:
            return UserData(self.postgres_db_url, email)
        except ValueError as e:
            self._log(f"Failed to retrieve user {email}. Does the user exist in the database?",
                      message=str(e))

if __name__=="__main__":
    import time

    # DataStorePost tests
    postgres_db_url = input("Enter Postgres url: ")

    test_data_store_post = DataStorePost(postgres_db_url, verbose=False)

    test_data_store_post.get_recent_posts(time.time())

    print("https://www.reddit.com/r/canada/comments/1eszy4e/pierre_poilievre_promises_to_defund_the_cbc_after/" in test_data_store_post)
    print(test_data_store_post["https://www.reddit.com/r/canada/comments/1eszy4e/pierre_poilievre_promises_to_defund_the_cbc_after/"])

    print("Bruh moment" in test_data_store_post)

    try:
        print(test_data_store_post["Bruh moment"])
    except ValueError:
        print("Bruh moment not in data store")

    test_data_store_post.insert_post("Bruh moment", "embed", "text", 100)

    print(test_data_store_post["Bruh moment"])

    # DataStoreUser tests

    test_data_store_user = DataStoreUser(postgres_db_url, verbose=False)

    user: UserData = test_data_store_user["contentcuratorauth@gmail.com"]
    print(test_data_store_user["contentcuratorauth@gmail.com"])

    try:
        print(test_data_store_user["bruhmoment@gmail.com"])
    except ValueError:
        print("bruhmoment@gmail.com not in data store")
    
    newuser: UserData = test_data_store_user.create_user("bruhmoment@gmail.com", return_user=True)

    print(newuser)
    print(test_data_store_user["contentcuratorauth@gmail.com"].curation_modes)