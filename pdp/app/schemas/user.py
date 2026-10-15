from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID


class UserRequest(BaseModel):
    username: str
    first_name: str
    last_name: str
    email: str
    email_verified: bool
    credentials: Dict[str, Any]
    enabled: bool


class UserCreateDB(BaseModel):
    idp_ref: str
    idp_issuer: str


class UserData(BaseModel):
    principal_id: UUID = Field(...)
    idp_ref: str
    idp_issuer: str
    created_at: datetime

    model_config = {
        "from_attributes": True, #ORM compatibility
        "population_by_name": True # support for aliases
    }


class UserResponse(BaseModel):
    success: bool = True
    data: UserData


class UserListResponse(BaseModel):
    success: bool = True
    data: List[UserData]