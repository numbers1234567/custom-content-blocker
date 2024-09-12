from typing import Generator
from .SocialClient import SocialClient, PostGetter
import json
import requests
import time
import base64

def clean_image_url(url : str) -> str:
    return url.replace("&amp;", "&")

class YoutubePostGetter(PostGetter):
    def __init__(self, post, verbose=True):
        pass

    def get_embed_html(self):
        pass

    
    def get_imgs_b64(self) -> list[str]:
        pass
    
    def get_text(self) -> str:
        pass

    def get_create_utc(self) -> int:
        pass
    
    def get_post_id(self) -> str:
        pass

class YoutubeClient(SocialClient):
    def __init__():
        super().__init__()
        pass

    def post_generator(self, count:int=100) -> Generator[PostGetter, None, None]:
        pass
            

        