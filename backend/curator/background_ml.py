import threading
import time
from typing import Iterable,Tuple,List
import numpy as np
import psycopg2

from sklearn.feature_extraction.text import CountVectorizer

# Background workers for automated ML activities

class MLBackgroundProcessor:
    def __init__(self, period: float=2, verbose: bool=False):
        self._verbose = verbose
        self.period_ns = period*1e9

    def _log(self, text: str, message:str|None=None):
        if not self._verbose: return
        print(f"[LOG-{self}]: {text}")
        if message:
            print(f"   Message: {message}")

    def update(self):
        raise NotImplementedError("update has not been implemented!")

    def _mainloop(self):
        last_run = 0
        while True:
            if self.period_ns > time.time_ns()-last_run:
                time.sleep((self.period_ns - time.time_ns() + last_run)/1e9)
            elif last_run > 0:
                self._log("Failed to hit deadline!")

            last_run = time.time_ns()
            try:
                self.update()
            except Exception as e:
                self._log("Update failed",
                          message=e)

    def start(self):
        mainloop = threading.Thread(target=lambda: self._mainloop())
        mainloop.start()

        return mainloop
    
class NGramFreqWorker(MLBackgroundProcessor):
    def __init__(self, postgres_db_url: str, period: float=2, verbose: bool=False):
        super().__init__(period=period, verbose=verbose)
        self.postgres_db_url = postgres_db_url
        self.df_vectorizers = [
            CountVectorizer(ngram_range=(i,i))
            for i in range(1,7)
        ]
        
    def insert_df(self, post_id: int, n_gram: str, n: int, freq: int):
        with psycopg2.connect(self.postgres_db_url) as conn:
            cur = conn.cursor()
            cur.execute("""
                INSERT INTO doc_freq (post_id,n_gram,num_tokens,freq)
                VALUES (%s,%s,%s,%s);
            """, (post_id, n_gram, n, freq))

            conn.commit()
            cur.close()
    
    def get_df_unprocessed_posts(self) -> List[Tuple[int,str]]:
        with psycopg2.connect(self.postgres_db_url) as conn:
            cur = conn.cursor()

            cur.execute("""
                SELECT internal_id, title
                FROM social_post_data
                WHERE internal_id NOT IN (
                    SELECT DISTINCT internal_id
                    FROM doc_freq LIMIT 400
                )
                ORDER BY internal_id DESC
                LIMIT 100;
            """)

            cur.close()
            target_posts: List[Tuple[int,str]] = list(cur.fetchall())

            return target_posts
        
    def insert_df_post(self, post_id: int, text: str):
        for n_gram_n,vectorizer in enumerate(self.df_vectorizers, start=1):
            # A lot of overhead, but it works and matches the evaluation procedure
            vectorized = vectorizer.fit_transform([text])
            for n_gram,freq in zip(vectorizer.get_feature_names_out(), vectorized.toarray()[0]):
                self.insert_df(post_id, n_gram, n_gram_n, int(freq))

    def update(self):
        target_posts = self.get_df_unprocessed_posts()

        for post_id,text in target_posts:
            self.insert_df_post(post_id, text)

if __name__=="__main__":
    import sys
    sys.path.append("..")
    from backend_shared.data_store import *

    try:
        data_store_post = DataStorePost("postgres://postgres:1234@localhost:5432/postgres")
        post: PostData = data_store_post.insert_post("some post on reddit", "", "hello world!", 0, return_post=True)
    except ValueError:
        post: PostData = data_store_post["some post on reddit"]
        print("Post already exists")
    freq_worker = NGramFreqWorker("postgres://postgres:1234@localhost:5432/postgres")
    freq_worker.insert_df_post(post.internal_id, "some post on reddit, this does not match the other one")