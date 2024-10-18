from typing import List, Dict, Optional, Union
from pydantic import BaseModel

class Meta(BaseModel):
    code: int
    message: str

class ResponseModel(BaseModel):
    data: Union[Dict, List[Dict], None]
    meta: Meta

class CheckReqPayload(BaseModel):
    role: str

class QAPairPayloadModel(BaseModel):
    question: str
    answer: str

class JDPayModel(BaseModel):
    role: str
    responsibilities: List[str]
    qualifications: List[str]
    technologies: List[str]
    experience: List[str]
    iscontract: bool
    salary_range: str
    currency: str
    working_mode: str
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None
    qa_pair: Optional[List[QAPairPayloadModel]] = None

class InputsModel(BaseModel):
    role: str
    responsibilities: List[str]
    qualifications: List[str]
    technologies: List[str]
    experience: List[str]

class RangePayModel(BaseModel):
    role: str
    iscontract: bool
    # location_id: Optional[str] = None
    city: Optional[str] = None
    state: Optional[str] = None
    country: Optional[str] = None

class CustomChoicesPayModel(BaseModel):
    question: str
    role: str

class RolePayModel(BaseModel):
    keyword: str

class PredefinedPayModel(BaseModel):
    job_title: str