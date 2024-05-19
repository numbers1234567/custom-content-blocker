from pydantic import BaseModel

class Media(BaseModel):
    content : str
    dataFormat : str

class MediaData(BaseModel):
    text : str
    images : list[Media] = []
    video : list[Media] = []

class Metadata(BaseModel):
    id : str

class PostData(BaseModel):
    media : MediaData
    metadata : Metadata