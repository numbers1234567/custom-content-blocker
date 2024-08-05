from typing import Generator
import praw
from .SocialClient import SocialClient, PostGetter
import json
import requests
import time
import base64

def clean_image_url(url : str) -> str:
    return url.replace("&amp;", "&")

class RedditPostGetter(PostGetter):
    def __init__(self, post):
        self.post = post
        self.permalink = post.permalink
        print(self.get_post_id())
        print(requests.get((self.get_post_id()[:-1] + ".json").replace("/.json", ".json")).content)
        self.post_json = json.loads(requests.get((self.get_post_id()[:-1] + ".json").replace("/.json", ".json")).content)

    def get_embed_html(self):
        reformatted_url = f"https://www.reddit.com{self.permalink}"
        
        reformatted_url.replace(":", "%3A").replace("/", "%2F")
        return json.loads(requests.get(f'https://www.reddit.com/oembed?url={reformatted_url}').content)["html"]

    
    def get_imgs_b64(self) -> list[str]:
        base_url = self.post.url
        img_urls = []
        # It is a single image
        if "i.redd.it" in base_url:
            img_urls.append(base_url)

        # It is a gallery of images
        try:  # Possible things could go wrong with all of these accesses
            for _,im_versions in self.post_json[0]["data"]["children"][0]["data"]["media_metadata"].items():
                best_version = (-1000, "")  # (size, url)
                for version in im_versions['p'] + [im_versions['s']]:
                    size = version["x"]*version["y"]
                    if size > 1000*1000: continue  # Too big 

                    best_version = max(best_version, (size, version['u']))
                if best_version[0] > 0:
                    img_urls.append(clean_image_url(best_version[1]))

        except Exception as e:
            print(f"[LOG]: Could not find gallery images for {self.get_post_id()}!")
            print("   Error: " + str(e))

        # Convert images
        imgs_b64 = []
        for url in img_urls:
            try:
                imgs_b64.append(base64.encodebytes(requests.get(url).content))
            except:
                print(f"[ERROR]: Failed to retrieve image {url} for {self.get_post_id()}!")
                print("   Error: " + str(e))

        return imgs_b64
    
    def get_text(self) -> str:
        return self.post.title

    def get_create_utc(self) -> int:
        return int(self.post.created_utc)
    
    def get_post_id(self) -> str:
        return 'https://www.reddit.com' + self.permalink

class RedditClient(SocialClient):
    def __init__(
        self, 
        client_id : str, 
        client_secret : str, 
        password : str, 
        username : str,
        user_agent : str,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            password=password,
            user_agent=user_agent,
            username=username
        )

    def post_generator(self, count:int=100) -> Generator[PostGetter, None, None]:
        for post in self.reddit.subreddit("popular").hot(limit=count):
            try:
                yield RedditPostGetter(post)
            except Exception as e:
                print(f"[ERROR]: Failed to retrieve post {post.permalink}!")
                print("   Message: " + str(e))
            

        