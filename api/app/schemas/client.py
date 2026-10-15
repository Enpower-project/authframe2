from pydantic import BaseModel
from typing import List, Dict, Any

class ClientCreateRequest(BaseModel):
     client_id: str
     redirect_uris: List[str]
     base_url: str
     admin_url: str
     secret: str
     enabled: bool


class ClientUpdateRequest(BaseModel):
     client_name: str
     redirect_uris: List[str]
     base_url: str
     admin_url: str
     secret: str
     enabled: bool
