from pydantic import BaseModel

class Subject(BaseModel):
    id: str
    claims: dict

class Resource(BaseModel):
    type: str
    id: str
    tenant: str

class DecisionRequest(BaseModel):
    subject: Subject
    resource: Resource
    action: str
    context: dict = {}
