from locust import HttpUser, task, between, constant
import argparse
from pandas import read_csv
import random

from dotenv import load_dotenv

from typing import List,Dict
import os

# Get test user emails
user_emails : List[str] = list(read_csv("test_user_data.csv", sep="\t")["email"])
post_times : List[int] = list(read_csv("test_post_data.csv", sep="\t")["create_utc"])
curation_modes : List[str] = ["all", "politics_only", "no_politics"]

class QuickstartUser(HttpUser):
    # Assumes that we are targeting some staging environment, so a token is not needed
    wait_time = between(1, 3)

    def on_start(self):
        self.credentials : Dict[str,str] = {"token" : "public", "email" : "public"}
        self.client.post(f"/login", json={"credentials": self.credentials})

    @task
    def test_curate(self):
        self.client.post(f"/get_curated_posts", 
            json={
                "credentials" : self.credentials,
                "curation_settings" : {
                    "curation_mode" : {
                        "key" : random.choice(curation_modes[1:]),
                        "name" : "bruh",
                    },
                    "social_media_whitelist" : [],
                    "trending_filters" : [],
                },
                "options" : {
                    "before" : random.choice(post_times),
                    "count_max" : 10,
                    "count_min" : 1,
                },
            }
        )

    @task
    def test_all(self):
        self.client.post(f"/get_curated_posts", 
            json={
                "credentials" : self.credentials,
                "curation_settings" : {
                    "curation_mode" : {
                        "key" : curation_modes[0],
                        "name" : "bruh",
                    },
                    "social_media_whitelist" : [],
                    "trending_filters" : [],
                },
                "options" : {
                    "before" : random.choice(post_times),
                    "count_max" : 10,
                    "count_min" : 1,
                },
            }
        )