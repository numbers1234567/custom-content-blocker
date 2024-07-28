import praw
from .SocialClient import SocialClient, SocialPostData, SocialPostMediaData, SocialPostMetaData
import json
import requests
import time

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

    def get_html_embed(self, permalink : str):
        reformatted_url = f"https://www.reddit.com{permalink}"
        
        reformatted_url.replace(":", "%3A").replace("/", "%2F")
        return json.loads(requests.get(f'https://www.reddit.com/oembed?url={reformatted_url}').content)["html"]

    def get_relevant_posts(self):
        popular_posts = self.reddit.subreddit("popular").hot(limit=100)
        posts = []
        for post in popular_posts:
            permalink = post.permalink
            embed_html = self.get_html_embed(permalink)
            post_id = 'https://www.reddit.com' + permalink
            create_utc = int(post.created_utc)

            media_data = SocialPostMediaData(embed_html)
            metadata   = SocialPostMetaData(create_utc, post_id)
            posts.append(SocialPostData(metadata, media_data))
            time.sleep(2)

        return posts