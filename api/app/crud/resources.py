from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone
from fastapi import HTTPException
from app.models import access
from app.models import consent
from app.schemas.resource import ResourceCreateRequest, ResourceData
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def create_resource(db: Session, resource: ResourceCreateRequest):
    db_resource = access.Resource(**resource.model_dump())
    db.add(db_resource)
    db.commit()
    db.refresh(db_resource)
    return ResourceData.model_validate(db_resource)


def get_all_resources(db: Session):
    return db.query(access.Resource).all()


def get_resource(db: Session, resource_id: UUID):
    db_resource = db.query(access.Resource).filter(
        access.Resource.resource_id == resource_id
    ).one_or_none()

    return ResourceData.model_validate(db_resource)


def get_resource_consents(db: Session, resource_id: UUID):
    consents = db.query(consent.Consent).filter(
        consent.Consent.resource_id == resource_id
    ).all()

    if consent is None:
        raise HTTPException(status_code=404, detail="No existing consents for resource_id found")
    
    return consents

