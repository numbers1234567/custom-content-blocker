from pydantic import BaseModel
from typing import List,Tuple

class Credentials(BaseModel):
    token : str|None=None
    email : str|None=None

class GetBLIPHeadRequestBody(BaseModel):
    curate_key : str

class BLIPParams(BaseModel):
    weight1 : List[List[float]]  # [768][10]
    weight2 : List[List[float]]  # [10][2]
    bias1 : List[float]  # [10]
    bias2 : List[float]  # [2]

class GetBLIPHeadResponseBody(BaseModel):
    params : BLIPParams

class GetBLIPHeadResponseBody(BaseModel):
    params : BLIPParams

class CurateModeChangeData(BaseModel):
    blip_params : BLIPParams|None

class UpdateCurateModeRequestBody(BaseModel):
    curate_key : str
    change_data : CurateModeChangeData

class UpdateCurateModeResponseBody(BaseModel):
    pass

class HTMLEmbed(BaseModel):
    html : str
    create_utc : int
    post_id : str

class GetRecentPostsResponseBody(BaseModel):
    html_embeds : List[HTMLEmbed]

class SignUpUserRequestBody(BaseModel):
    credentials : Credentials

class SignUpUserResponseBody(BaseModel):
    success : bool

class GetUserDataRequestBody(BaseModel):
    email : str

class CurationMode(BaseModel):
    key : str
    name : str
    
class GetUserDataResponseBody(BaseModel):
    email : str
    uid : int
    create_utc : int
    curate_modes : List[CurationMode]


class CurationSetting(BaseModel):
    curation_mode : CurationMode
    social_media_whitelist : list[CurationMode]
    trending_filters : list[CurationMode]

class CuratePostsRequestOptions(BaseModel):
    before : int  # UTC
    count_max : int = 10
    count_min : int = 5
    max_score : float = 0.5

# get_curated_posts
class CuratePostsRequestBody(BaseModel):
    credentials : Credentials
    curation_settings : CurationSetting
    options : CuratePostsRequestOptions

class CuratedPost(BaseModel):
    post_id : str
    create_utc : int
    html : str
    curate_score : float
    
class CuratedPostBatch(BaseModel):
    posts : list[CuratedPost]

class CuratedPostsResponseBody(CuratedPostBatch):
    pass

class GetCurateScoreResponseBody(BaseModel):
    curate_score : float

class RecommendData(BaseModel):
    positive : bool  # Positive in the sense that this is a "good" post

class RecommendPostRequestBody(BaseModel):
    credentials : Credentials|None=None
    curate_key : str
    post_id : str
    options : RecommendData

class RecommendPostResponseBody(BaseModel):
    pass

class CreateCurationModeRequestBody(BaseModel):
    credentials : Credentials
    mode_name : str

class CreateCurationModeResponseBody(BaseModel):
    curation_mode : CurationMode

class DeleteCurationModeRequestBody(BaseModel):
    credentials : Credentials
    curation_key : str

class DeleteCurationModeResponseBody(BaseModel):
    pass

class LoginRequestBody(BaseModel):
    credentials : Credentials

class LoginResponseBody(BaseModel):
    success : bool

class GetCurationModesRequestBody(BaseModel):
    credentials : Credentials

class GetCurationModesResponseBody(BaseModel):
    curation_modes : List[CurationMode]
    emerging_topics : List[CurationMode]

class GetCurateScoreRequestBody(BaseModel):
    curation_settings : CurationSetting
    post_id : str|None=None
    post_ids : List[str]|None=None

class PostScore(BaseModel):
    score : float
    post_id : str
    success : bool

class GetCurateScoreResponseBody(BaseModel):
    scores : List[PostScore]