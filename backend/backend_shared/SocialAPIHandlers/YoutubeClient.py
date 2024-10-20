from typing import Generator
from .SocialClient import SocialClient, PostGetter
import json
import requests
import time
import base64
from datetime import datetime

class YoutubePostGetter(PostGetter):
    def __init__(self, post_id: str|None=None, post_data: dict|None=None, verbose=True):
        assert post_id or post_data
        
        if not post_id:  # post_id should be in the form "Youtube: [youtube-video-id]". post_data should be set
            post_id = "Youtube: " + post_data["id"]
        elif not post_data:  # post_data is not set, but we can get it from the post_id and youtube's API
            y_id = self.post_id.replace("Youtube:", "").strip()
            url = f"https://youtube.googleapis.com/youtube/v3/videos?part=snippet%2CcontentDetails%2Cstatistics%2Cplayer&chart=mostPopular&id={y_id}&key={self.yt_data_key}"
            response = requests.get(
                url,
                headers={"Accept": "application/json"}
            )
            response = json.loads(response.content)

            post_data = response["items"][0]

        self.post_data = post_data
        self.post_id = post_id

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
        return int((datetime.strptime(self.post_data["snippet"]["publishedAt"], "%Y-%m-%dT%H:%M:%SZ") - datetime(1970, 1, 1)).total_seconds())
    
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
                    yield YoutubePostGetter(post_data=video)
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