from pydantic import BaseModel, Field
from datetime import datetime
from typing import List, Dict, Any, Optional
from uuid import UUID



class TenantCreate(BaseModel):
    slug: str
    name: str
    status: str


class TenantData(BaseModel):
    tenant_id: UUID = Field(...)
    slug: str
    name: str
    status: str
    created_at: datetime
    updated_at: datetime

    model_config = {
        "from_attributes": True, #ORM compatibility
        "population_by_name": True # support for aliases
    }


class TenantResponse(BaseModel):
    success: bool = True
    data: TenantData


class TenantListResponse(BaseModel):
    success: bool = True
    data: List[TenantData]