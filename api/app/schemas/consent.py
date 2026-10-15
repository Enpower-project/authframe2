from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID

class ConsentRequestCreate(BaseModel):
    resource_id: str
    scope: str
    purpose: str
    owner_id: str
    requesting_party_id: str
    client_id: str
    validity_until: str


class ConsentRequestData(BaseModel):
    consent_request_id: UUID = Field(..., alias="id")
    resource_id: UUID
    scope: str
    purpose: str
    owner_id: UUID
    requesting_party_id: UUID
    client_id: UUID
    request_status: str
    validity_until: Optional[datetime] = None
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True, #ORM compatibility
        "population_by_name": True # support for aliases
    }


class PermissionCreate(BaseModel):
    id: UUID = Field(..., alias="id")


class PolicyCreate(BaseModel):
    id: UUID = Field(..., alias="id")


class PermissionData(BaseModel):
    id: UUID = Field(..., alias="id")
    granted_at: datetime

    model_config = {
        "from_attributes": True, #ORM compatibility
        "population_by_name": True # support for aliases
    }


class PolicyData(BaseModel):
    id: UUID = Field(..., alias="id")
    granted_at: datetime

    model_config = {
        "from_attributes": True, #ORM compatibility
        "population_by_name": True # support for aliases
    }


class ConsentRequestResponse(BaseModel):
    success: bool = True
    data: ConsentRequestData


class ConsentRequestListResponse(BaseModel):
    success: bool = True
    data: List[ConsentRequestData]


class WithdrawRequest(BaseModel):
    reason: str


class ConsentCreate(BaseModel):
    resource_id: str
    scope: str
    purpose: str
    given_by: str
    given_to: str
    client_id: str
    consent_status: str
    validity_until: str


class ConsentData(BaseModel):
    consent_id: UUID = Field(..., alias="id")
    resource_id: UUID
    scope: str
    purpose: str
    given_by: UUID
    given_to: UUID
    client_id: UUID
    consent_status: str
    reason: Optional[str] = None
    validity_until: Optional[datetime] = None
    timestamp: datetime
    timestamp_updated: datetime

    model_config = {
        "from_attributes": True, #ORM compatibility
        "population_by_name": True # support for aliases
    }


class ConsentResponse(BaseModel):
    success: bool = True
    data: ConsentData


class ConsentListResponse(BaseModel):
    success: bool = True
    data: List[ConsentData]