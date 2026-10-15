from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.orm import Session
from app.db.session import SessionLocal
from app.schemas.audit import LogEvent
from app.auth.dependencies import require_token
from fastapi import Depends
from fastapi.responses import JSONResponse
import logging

from app.keycloak_instance import kc

logger = logging.getLogger(__name__)


router = APIRouter(prefix="/audit", tags=["audit"])


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@router.get("", response_model=list[LogEvent])
def get_audit_logs(db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    return None

@router.get("/{request_id}", response_model=LogEvent)
def get_log_for_requestid(request_id: str, db: Session = Depends(get_db), token=Depends(require_token("admin"))):
    return None

