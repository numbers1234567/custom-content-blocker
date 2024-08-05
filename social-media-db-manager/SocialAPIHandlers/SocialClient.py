"""
General getters for social apps

Use of generators to reduce memory usage (loading in many images)
"""
from dataclasses import dataclass,field
from typing import Generator
import time

@dataclass
class SocialPostBaseMetaData:
    create_utc : int
    # Unique internal post ID which can be used to find the source
    post_id : str

@dataclass
class SocialPostBaseMediaData:
    embed_html : str = ""
    text : str = ""
    # Images in base 64 format, a typical way to transfer image data on the web
    images_b64 : list[str] = field(default_factory=lambda: [])

@dataclass
class SocialPostBaseData:
    metadata   : SocialPostBaseMetaData
    media_data : SocialPostBaseMediaData

# Separate object to handle getting data from a specific post
class PostGetter:
    def get_embed_html(self) -> list[str]:
        pass

    def get_imgs_b64(self) -> list[str]:
        pass

    def get_text(self) -> str:
        pass

    def get_create_utc(self) -> int:
        pass

    def get_post_id(self) -> str:
        pass

class SocialClient:

    def __init__(self):
        pass

    def post_generator(self) -> Generator[PostGetter, None, None]:
        pass

    """
    Gets all posts that are currently trending on the social apps
    """
    def get_relevant_posts(self, count:int=100) -> Generator[SocialPostBaseData, None, None]:
        for post in self.post_generator():
            metadata = SocialPostBaseMetaData(post.get_create_utc(), post.get_post_id())
            media_data = SocialPostBaseMediaData(post.get_embed_html(), post.get_text(), post.get_imgs_b64())

            last_gen = time.time()
            try:
                yield SocialPostBaseData(metadata, media_data)
            except Exception as e:
                print(f"[ERROR]: Failed to retrieve post {post.get_post_id()}!")
                print("   Message: " + str(e))

            # Don't request too frequently
            elapsed = time.time()-last_gen
            if elapsed < 2:
                time.sleep(2-elapsed)