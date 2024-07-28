from dataclasses import dataclass,field

@dataclass
class SocialPostMetaData:
    create_utc : int
    post_id : str

@dataclass
class SocialPostMediaData:
    embed_html : str

@dataclass
class SocialPostData:
    metadata   : SocialPostMetaData
    media_data : SocialPostMediaData

class SocialClient:
    def __init__(self):
        pass

    """
    Gets all posts that are currently trending on the social apps
    """
    def get_relevant_posts(self) -> list[SocialPostData]:
        pass

