import psycopg2
from dataclasses import dataclass,field

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

    def create_connection(self):  # No type annotation, but should return a psycopg2 connection
        return psycopg2.connect(self.postgres_db_url)

class DataStorePost(DataStore):
    def __init__(self, postgres_db_url, verbose=False):
        super().__init__(postgres_db_url, verbose=verbose)

        self.max_id_lock = threading.Lock()
        self.max_id = 0
        self._set_max_id()

    def _set_max_id(self):
        with self.create_connection() as conn:
            cur: psycopg2.cursor = conn.cursor()

            cur.execute("""
                SELECT MAX(internal_id)
                FROM social_post_data;
            """)

            result = cur.fetchone()

            self.max_id = result[0] if result[0]!=None else -1
            
            cur.close()

    def __contains__(self, post_id: str) -> bool:
        with self.create_connection() as conn:
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
            with self.create_connection() as conn:
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
        with self.create_connection() as conn:
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
        with self.create_connection() as conn:
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

class DataStoreUser(DataStore):
    def __init__(self, postgres_db_url, verbose=False):
        super().__init__(postgres_db_url, verbose=verbose)

if __name__=="__main__":
    import time

    postgres_db_url = input("Enter Postgres url: ")

    test_data_store = DataStorePost(postgres_db_url, verbose=True)

    test_data_store.get_recent_posts(time.time())

    print("https://www.reddit.com/r/canada/comments/1eszy4e/pierre_poilievre_promises_to_defund_the_cbc_after/" in test_data_store)
    print(test_data_store["https://www.reddit.com/r/canada/comments/1eszy4e/pierre_poilievre_promises_to_defund_the_cbc_after/"])

    print("Bruh moment" in test_data_store)

    try:
        print(test_data_store["Bruh moment"])
    except ValueError:
        print("Bruh moment not in data store")

    test_data_store.insert_post("Bruh moment", "embed", "text", 100)

    print(test_data_store["Bruh moment"])