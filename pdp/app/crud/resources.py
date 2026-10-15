from sqlalchemy.orm import Session
from sqlalchemy import or_
from datetime import datetime, timezone
from fastapi import HTTPException
from app.models import access
from uuid import UUID
import logging

logger = logging.getLogger(__name__)


def get_all_resources(db: Session):
    return db.query(access.Resource).all()


def get_resource_by_url(db: Session, url: str):
    db_resource = db.query(access.Resource).filter(
        access.Resource.url == url
    ).one_or_none()

    resource_id = None

    try:
        resource_id = db_resource.resource_id
    except Exception as e:
        logger.exception(f"e")

    return resource_id