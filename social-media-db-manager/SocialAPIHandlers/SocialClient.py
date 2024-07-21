from dataclasses import dataclass,field

@dataclass
class MetaData:
    pass

@dataclass
class MediaData:
    pass

@dataclass
class SocialPostData:
    pass

class SocialClient:
    def __init__(self):
        pass

    """
    Gets all posts that are currently trending on the social apps
    """
    def get_relevant_posts(self) -> list[SocialPostData]:
        pass

