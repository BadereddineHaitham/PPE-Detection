from typing import Optional
from pydantic import BaseModel, EmailStr, Field, ConfigDict
from .base import MongoBaseModel, PyObjectId

class UserBase(BaseModel):
    first_name: str
    last_name: str
    email: EmailStr

class UserCreate(UserBase):
    password: str = Field(..., min_length=8)

class UserLogin(BaseModel):
    email: EmailStr
    password: str

class UserInDB(MongoBaseModel, UserBase):
    hashed_password: str
    is_active: bool = True
    is_superuser: bool = False

class UserResponse(MongoBaseModel, UserBase):
    is_active: bool
    is_superuser: bool

    model_config = ConfigDict(from_attributes=True)

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    email: Optional[str] = None 