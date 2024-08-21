from pydantic import BaseModel
from typing import Dict, List


class HTMLEmbed(BaseModel):
    html : str
    create_utc : int
    post_id : str

class GetRecentPostsResponseBody(BaseModel):
    html_embeds : List[HTMLEmbed]

class CreateCurationModeRequestBody(BaseModel):
    user_id : int
    curation_name : str

class CreateCurationModeResponseBody(BaseModel):
    curation_key : str
    curation_name : str
    curation_id : int