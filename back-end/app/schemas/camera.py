from typing import List, Optional
from pydantic import BaseModel, Field, IPvAnyAddress
from .base import MongoBaseModel

class AlertClass(BaseModel):
    name: str
    confidence: float = Field(..., ge=0.0, le=1.0)
    threshold: float = Field(..., ge=0.0, le=1.0)

class CameraBase(BaseModel):
    name: str
    ip: str = Field(..., description="IP address of the camera")
    user_id: str = Field(..., description="ID of the user who owns this camera")
    alert_classes: List[AlertClass] = Field(default_factory=list)

class CameraCreate(CameraBase):
    pass

class CameraUpdate(BaseModel):
    name: Optional[str] = None
    ip: Optional[str] = None
    alert_classes: Optional[List[AlertClass]] = None

class CameraInDB(MongoBaseModel, CameraBase):
    pass

class CameraResponse(MongoBaseModel, CameraBase):
    pass