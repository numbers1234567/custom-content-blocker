from pydantic import BaseModel
from typing import List

class GetBLIPHeadRequestBody(BaseModel):
    curate_key : str

class BLIPParams(BaseModel):
    weight1 : List[List[float]]  # [768][10]
    weight2 : List[List[float]]  # [10][2]
    bias1 : List[float]  # [10]
    bias2 : List[float]  # [10]

class GetBLIPHeadResponseBody(BaseModel):
    params : BLIPParams

class BLIPParams(BaseModel):
    weight1 : List[List[float]]  # [768][10]
    weight2 : List[List[float]]  # [10][2]
    bias1 : List[float]  # [10]
    bias2 : List[float]  # [10]

class GetBLIPHeadResponseBody(BaseModel):
    params : BLIPParams

class CurateModeChangeData(BaseModel):
    blip_params : BLIPParams|None

class UpdateCurateModeRequestBody(BaseModel):
    curate_key : str
    change_data : CurateModeChangeData

class UpdateCurateModeResponseBody(BaseModel):
    pass