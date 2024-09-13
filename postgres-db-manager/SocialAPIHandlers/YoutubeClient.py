from typing import Generator
from .SocialClient import SocialClient, PostGetter
import json
import requests
import time
import base64
from datetime import datetime

class YoutubePostGetter(PostGetter):
    def __init__(self, post_data, verbose=True):
        self.post_data = post_data

    def get_embed_html(self) -> str:
        return self.post_data["player"]["embedHtml"]
    
    def get_imgs_b64(self) -> list[str]:
        # Valid thumbnail key by priority
        thumbnail_keys = ["standard", "high", "medium", "default", "maxres"]

        for thumbnail_key in thumbnail_keys:
            try:
                img_url = self.post_data["snippet"]["thumbnails"][thumbnail_key]["url"]
                image_raw = requests.get(img_url).content

                # Success
                return [base64.encodebytes(image_raw).decode('utf-8')]

            except Exception as e:
                print(f"[ERROR]: Failed to retrieve thumbnail of {self.get_post_id()} with key {thumbnail_key}.")
                print("   Message: " + str(e))
        
        print(f"[LOG]: Could not find thumbnail for {self.get_post_id()}.")
        return []
    
    def get_text(self) -> str:
        return self.post_data["snippet"]["title"]

    def get_create_utc(self) -> int:
        return int((datetime.strptime('2024-09-07T17:46:16Z', "%Y-%m-%dT%H:%M:%SZ") - datetime(1970, 1, 1)).total_seconds())
    
    def get_post_id(self) -> str:
        return "YouTube: " + self.post_data["id"]

class YoutubeClient(SocialClient):
    def __init__(self, yt_data_key):
        super().__init__()
        self.yt_data_key = yt_data_key

    def post_generator(self, count:int=200) -> Generator[PostGetter, None, None]:
        url = f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet%2CcontentDetails%2Cstatistics%2Cplayer&chart=mostPopular&regionCode=US&key={self.yt_data_key}&maxResults=50" 
        total_yield = 0
        last_req = 0
        while True:
            response = requests.get(
                url,
                headers={"Accept": "application/json"}
            )
            response = json.loads(response.content)
            
            for video in response["items"]:
                if total_yield >= count: break
                try:
                    if time.time() - last_req <= 2:
                        time.sleep(2 - (time.time() - last_req))
                    yield YoutubePostGetter(video)
                    last_req = time.time()
                    total_yield += 1
                except Exception as e:
                    print(f"[ERROR]: Failed to retrieve a popular YouTube post with request url {url}")
                    print("   Message: " + str(e))

            if "nextPageToken" not in response.keys() or total_yield >= count:
                # End of list
                break

            nextPageToken = response["nextPageToken"]
            url = f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet%2CcontentDetails%2Cstatistics%2Cplayer&chart=mostPopular&regionCode=US&key={self.yt_data_key}&maxResults=50&pageToken={nextPageToken}"