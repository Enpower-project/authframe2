from pydantic import BaseModel, Field
from typing import List, Dict, Any
from datetime import datetime
from uuid import UUID


class ResourceCreateRequest(BaseModel):
    tenant_id: UUID = Field(...)
    owner_id: UUID = Field(...)
    type: str
    name: str
    url: str
    description: str


class ResourceData(BaseModel):
    resource_id: UUID
    tenant_id: UUID
    owner_id: UUID
    type: str
    name: str
    url: str
    description: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True, #ORM compatibility
        "population_by_name": True # support for aliases
    }


class ResourceResponse(BaseModel):
    success: bool = True
    data: ResourceData


class ResourceListResponse(BaseModel):
    success: bool = True
    data: List[ResourceData]



# class ResourceUpdateRequest(BaseModel):
#     resource_name: str
#     resource_type: str
#     resource_uris: List[str]
#     resource_scopes: List[str]
#     resource_attributes: Dict[str, Any]
#     owner_managed_access: bool