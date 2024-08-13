from pydantic import BaseModel

class CurationMode(BaseModel):
    key : str
    name : str

class Credentials(BaseModel):
    token : str

class CurationSetting(BaseModel):
    curation_mode : CurationMode
    social_media_whitelist : list[CurationMode]
    trending_filters : list[CurationMode]

class CuratePostsRequestOptions(BaseModel):
    before : int  # UTC
    count_max : int = 10
    count_min : int = 5
    min_score : float = 0.5

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

class CreateCurationModeRequestBody(BaseModel):
    credentials : Credentials
    mode_name : str
    preset_key : str|None = None

class CreateCurationModeResponseBody(BaseModel):
    curation_mode : CurationMode

class LoginRequestBody(BaseModel):
    credentials : Credentials

class LoginResponseBody(BaseModel):
    success : bool