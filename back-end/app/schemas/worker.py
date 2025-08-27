from typing import Optional
from pydantic import BaseModel, Field
from .base import MongoBaseModel

class WorkerBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    image: str = Field(..., description="Base64 encoded image or image URL")
    user_id: str = Field(..., description="ID of the user who owns this worker")

class WorkerCreate(WorkerBase):
    pass

class WorkerUpdate(BaseModel):
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    image: Optional[str] = Field(None, description="Base64 encoded image or image URL")

class WorkerInDB(MongoBaseModel, WorkerBase):
    pass

class WorkerResponse(MongoBaseModel, WorkerBase):
    pass