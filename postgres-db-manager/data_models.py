from pydantic import BaseModel
from typing import Dict, List


class HTMLEmbed(BaseModel):
    html : str
    create_utc : int
    post_id : str
    
class GetRecentPostsResponseBody(BaseModel):
    html_embeds : List[HTMLEmbed]