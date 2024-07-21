import praw
from .SocialClient import SocialClient

class RedditClient(SocialClient):
    def __init__(
        self, 
        client_id : str, 
        client_secret : str, 
        password : str, 
        username : str,
        platform : str,
        app_name : str, 
        version : str,
        **kwargs
    ):
        super().__init__(**kwargs)
        self.reddit = praw.Reddit(
            client_id=client_id,
            client_secret=client_secret,
            password=password,
            user_agent=f"{platform}:{app_name}:{version} (by /u/{username})",
            username=username
        )

    def get_html_embed(permalink : str):
        pass

    def get_relevant_posts(self):
        return super().get_posts()