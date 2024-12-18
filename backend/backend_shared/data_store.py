import psycopg2
import psycopg2.pool
from contextlib import contextmanager
from dataclasses import dataclass,field

import random

from typing import List,Generator

from functools import cache
import threading

import time

try:
    from .data_models import CurationMode
except:
    from data_models import CurationMode

class DataStore:
    def __init__(self, postgres_db_url: str|None=None, conn_pool: psycopg2.pool.AbstractConnectionPool|None=None, minconn: int=2, maxconn: int=2, verbose: bool=False):
        assert postgres_db_url or conn_pool
        
        if not conn_pool:
            # Construct connection pool for this DataStore
            s = postgres_db_url.replace("postgres://", "")
            [credentials,db_string] = s.split("@")
            [user,password] = credentials.split(":")
            [addr,db_name] = db_string.split("/")
            [host,port] = addr.split(":")
            conn_pool = psycopg2.pool.ThreadedConnectionPool(
                minconn, maxconn,
                user=user,
                password=password,
                host=host,
                port=port,
                database=db_name,
            )

        self.conn_pool = conn_pool
        conn_pool._kwargs

        self._verbose = verbose
        
    def _log(self, text: str, message:str|None = None):
        if not self._verbose: return
        print(f"[LOG-{self}]: {text}")
        if message:
            print(f"   Message: {message}")

    @contextmanager
    def create_db_connection(self) -> Generator[psycopg2.extensions.connection, None, None]:  # No type annotation, but should return a psycopg2 connection
        # Busy-wait until connection is retrieved
        conn: psycopg2.extensions.connection|None = None
        while not conn:
            try:
                conn = self.conn_pool.getconn()
            except psycopg2.pool.PoolError as e:
                # Queries take a while, so 0.05 may be fine.
                time.sleep(0.05)
        assert conn

        try:
            yield conn
        finally:
            self.conn_pool.putconn(conn)
    
class PostData(DataStore):
    def __init__(self, conn_pool: psycopg2.pool.AbstractConnectionPool, internal_id: int|None=None, post_id: str|None=None, embed_html: str|None=None, text: str|None=None, create_utc: int|None=None, verbose: bool=False):
        assert internal_id or post_id
        super().__init__(conn_pool=conn_pool, verbose=verbose)

        self.internal_id: int = -1
        self.post_id: str = ""
        self.embed_html: str = ""
        self.text: str = ""
        self.create_utc: int = 0

        if internal_id==None:
            with self.create_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT internal_id
                    FROM social_post_data
                    WHERE post_id=%s;
                """, (self.post_id,))
                self.internal_id, = cur.fetchone()

        if internal_id: self.internal_id = internal_id
        if post_id: self.post_id = post_id
        if embed_html: self.embed_html = embed_html
        if text: self.text = text
        if create_utc: self.create_utc = create_utc

        if not post_id or not embed_html or not text or not create_utc:
            with self.create_db_connection() as conn:
                cur = conn.cursor()
                cur.execute("""
                    SELECT internal_id,post_id,title,embed_html,create_utc
                    FROM social_post_data
                    WHERE internal_id=%s;
                """, (self.internal_id,))
            _,self.post_id,self.text,self.embed_html,self.create_utc = cur.fetchone()

    def __repr__(self):
        return f"<PostData {self.post_id} - {self.internal_id}>"

class DataStorePost(DataStore):
    def __init__(self, postgres_db_url, minconn: int=5, maxconn: int=10, verbose=False):
        super().__init__(postgres_db_url, minconn=minconn, maxconn=maxconn, verbose=verbose)

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
    
    def insert_post(self, post_id: str, embed_html: str, text: str, create_utc: int, return_post: bool=False, _retries: int = 10) -> PostData|None:
        try:
            # This post "claims" add_id as its id
            with self.max_id_lock:
                add_id = self.max_id + 1
                self.max_id = add_id

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
                if return_post: return PostData(self.conn_pool, add_id, post_id, embed_html, text, create_utc, verbose=self._verbose)

        except psycopg2.IntegrityError as e:  # This should catch the max id being desynced for some reason
            if post_id in self:
                raise ValueError(f"{post_id} already exists in DB!")
            self._log(f"Failed to insert post {post_id} with internal id {add_id}. Retries left: {_retries}.",
                        message=str(e))
            if _retries > 0:
                self._set_max_id()

                return self.insert_post(post_id, embed_html, text, create_utc, return_post=return_post, _retries=_retries-1)
            
            else:
                raise Exception(f"Failed to insert {post_id} in DB!")

    def __getitem__(self, post_id: str) -> PostData:
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

            return PostData(
                conn_pool=self.conn_pool,
                internal_id=internal_id,
                post_id=post_id,
                embed_html=embed_html,
                text=text,
                create_utc=create_utc,
            )
    
    def get_recent_posts(self, before: int, count: int=20) -> List[PostData]:
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
            PostData(
                conn_pool=self.conn_pool,
                internal_id=internal_id,
                post_id=post_id,
                embed_html=embed_html,
                text=text,
                create_utc=create_utc,
            )
            for internal_id, post_id, text, embed_html, create_utc in result
        ]

class UserData(DataStore):
    # Curate id must be synced
    whitelist_key_characters = "qwertyuiopasdfghjklzxcvbnmQWERTYUIOPASDFGHJKLZXCVBNM"
    max_curate_id_lock = threading.Lock()
    def _set_max_curate_id(conn: psycopg2.extensions.connection):
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

    def __init__(self, conn_pool: psycopg2.pool.AbstractConnectionPool, email: str, create_utc: int=None, uid: int=None, curation_modes: List[CurationMode]|None=None, verbose: bool = False):
        super().__init__(conn_pool=conn_pool, verbose=verbose)

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
                self.curation_modes = [CurationMode(key=key, name=name) for key,name in curation_modes]

            except TypeError as e:
                raise ValueError(f"Failed to retrieve data for {self}. Does the user exist in the database?")

            cur.close()
    
    def create_curation_mode(self, name: str, _retries=10):
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
                with self.create_db_connection() as conn:
                    UserData._set_max_curate_id(conn)
                self.create_curation_mode(name, _retries=_retries-1)

    def delete_curation_mode(self, curate_key: str):
        with self.create_db_connection() as conn:
            cur = conn.cursor()

            cur.execute("""
                DELETE FROM curation_modes
                WHERE curation_key=%s;
            """, (curate_key,))
            conn.commit()

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

    def create_user(self, email: str, return_user=False, _retries=10) -> UserData|None:
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

                if return_user: return UserData(self.conn_pool, email, create_utc=create_time, uid=add_id, curation_modes=[], verbose=self._verbose)

        except psycopg2.IntegrityError as e:  # This should catch the max id being desynced for some reason
            self._log(f"Failed to insert user {email} with id {add_id}. Retries left: {_retries}.",
                      message=str(e))
            
            if _retries > 0:
                self._set_max_uid()
                return self.create_user(email, return_user=return_user, _retries=_retries-1)
        

    def __getitem__(self, email: str) -> UserData:
        try:
            return UserData(self.conn_pool, email)
        except ValueError as e:
            raise ValueError(f"Failed to retrieve data for {self}. Does the user exist in the database?")


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